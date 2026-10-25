"""Testes da janela grafica do cliente.

Rodam com a plataforma offscreen do Qt, sem abrir janela de verdade, e
sao ignorados automaticamente quando o PySide6 nao esta instalado. A
janela conversa com o servidor real atraves da mesma sessao de teste
usada em test_cliente.py, entao o que se verifica aqui e o comportamento
da interface: o que ela carrega, o que mostra na arvore e o que registra
no painel de padroes.
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from forum import rastro  # noqa: E402
from forum.criacional.singleton import Forum  # noqa: E402
from forum.estrutural.facade import ForumFacade  # noqa: E402
from servidor.app import criar_app  # noqa: E402
from testes.test_cliente import ENDERECO, SessaoDeTeste  # noqa: E402

try:
    from PySide6.QtWidgets import QApplication, QMessageBox

    from cliente.api import ApiForum
    from cliente.janela import JanelaPrincipal

    QT_DISPONIVEL = True
except ImportError:  # pragma: no cover - ambiente sem PySide6
    QT_DISPONIVEL = False


@unittest.skipUnless(QT_DISPONIVEL, "PySide6 nao esta instalado")
class TesteJanelaPrincipal(unittest.TestCase):
    aplicacao = None

    @classmethod
    def setUpClass(cls):
        cls.aplicacao = QApplication.instance() or QApplication([])

    def setUp(self):
        Forum.resetar()
        rastro.iniciar()
        app = criar_app(ForumFacade())
        app.config.update(TESTING=True)
        self.api = ApiForum(ENDERECO, sessao=SessaoDeTeste(app.test_client()))
        self._avisos = []
        # as caixas de dialogo sao modais: substituimos por um registro
        self._warning_original = QMessageBox.warning
        self._information_original = QMessageBox.information
        QMessageBox.warning = lambda *args, **kwargs: self._avisos.append(args[-1])
        QMessageBox.information = lambda *args, **kwargs: self._avisos.append(args[-1])

        self.api.cadastrar_usuario("ana", "ana@forum.com")
        self.api.cadastrar_usuario("bruno", "bruno@forum.com", "moderador")
        self.janela = JanelaPrincipal(self.api)

    def tearDown(self):
        QMessageBox.warning = self._warning_original
        QMessageBox.information = self._information_original
        self.janela.close()
        Forum.resetar()

    def selecionar_primeiro_topico(self):
        self.janela.lista_topicos.setCurrentRow(0)

    # --- carga inicial ------------------------------------------------------
    def test_carrega_usuarios_no_seletor(self):
        self.assertEqual(self.janela.combo_usuario.count(), 2)
        self.assertEqual(self.janela.usuario_atual, "ana")

    def test_lista_vazia_quando_nao_ha_topicos(self):
        self.assertEqual(self.janela.lista_topicos.count(), 0)
        self.assertIn("Listar topicos", self.janela.painel_rastro.toPlainText())

    def test_lista_topicos_apos_recarregar(self):
        self.api.abrir_topico("ana", "Recursao", "duvida", ["python"])
        self.janela.carregar_topicos()
        self.assertEqual(self.janela.lista_topicos.count(), 1)

    # --- arvore da discussao ------------------------------------------------
    def test_arvore_reflete_a_estrutura_recebida(self):
        topico = self.api.abrir_topico("ana", "Recursao", "duvida").dados
        mensagem = self.api.responder(topico["identificador"], "bruno", "use caso base").dados
        self.api.anexar(mensagem["identificador"], "bruno", "exemplo.py", 3)

        self.janela.carregar_topicos()
        self.selecionar_primeiro_topico()

        raiz = self.janela.arvore.topLevelItem(0)
        self.assertEqual(raiz.childCount(), 1)
        self.assertEqual(raiz.child(0).childCount(), 1)
        self.assertIn("ANEXO", raiz.child(0).child(0).text(0))
        self.assertIn("Recursao", self.janela.rotulo_discussao.text())

    def test_painel_registra_os_padroes(self):
        self.api.abrir_topico("ana", "Observer", "duvida")
        self.janela.painel_rastro.clear()
        self.janela.carregar_topicos()
        self.selecionar_primeiro_topico()
        painel = self.janela.painel_rastro.toPlainText()
        self.assertIn("[Strategy]", painel)
        self.assertIn("[Composite]", painel)

    # --- acoes e erros ------------------------------------------------------
    def test_votar_sem_selecao_avisa(self):
        self.janela.votar()
        self.assertTrue(self._avisos)

    def test_votar_em_topico_e_recusado_pelo_servidor(self):
        self.api.abrir_topico("ana", "Votos", "duvida")
        self.janela.carregar_topicos()
        self.selecionar_primeiro_topico()
        self.janela.votar()
        self.assertTrue(any("mensagens" in str(aviso).lower() for aviso in self._avisos))

    def test_inscrever_usuario_atual(self):
        self.api.abrir_topico("ana", "Observer", "duvida")
        self.janela.carregar_topicos()
        self.selecionar_primeiro_topico()
        self.janela.combo_usuario.setCurrentIndex(
            self.janela.combo_usuario.findText("bruno")
        )
        self.janela.inscrever()
        arvore = self.api.obter_topico(1).dados
        self.assertEqual(sorted(arvore["inscritos"]), ["ana", "bruno"])

    def test_alterar_estado_pela_janela(self):
        self.api.abrir_topico("ana", "Estado", "duvida")
        self.janela.carregar_topicos()
        self.selecionar_primeiro_topico()
        self.janela.combo_estado.setCurrentIndex(
            self.janela.combo_estado.findData("fechar")
        )
        self.janela.alterar_estado()
        self.assertEqual(self.api.obter_topico(1).dados["estado"], "Fechado")

    def test_falha_de_servidor_mostra_aviso(self):
        class SessaoQuebrada:
            def request(self, *_args, **_kwargs):
                import requests

                raise requests.ConnectionError("sem servidor")

        self.janela.api = ApiForum(ENDERECO, sessao=SessaoQuebrada())
        self.janela.carregar_topicos()
        self.assertTrue(self._avisos)
        self.assertIn("FALHOU", self.janela.painel_rastro.toPlainText())


if __name__ == "__main__":
    unittest.main(verbosity=2)
