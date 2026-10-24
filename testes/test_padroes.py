"""Testes automatizados dos nove padroes de projeto.

Execucao a partir da raiz do repositorio:

    python -m unittest discover -s testes -v
"""

import io
import unittest
from contextlib import redirect_stdout

from forum.comportamental.observer import NotificadorDeUsuario, RegistroDeAtividade
from forum.comportamental.state import Aberto, Arquivado, Fechado
from forum.comportamental.strategy import (
    ListagemDeTopicos,
    PorMaisRecentes,
    PorMaisRespondidos,
    PorMaisVotados,
)
from forum.criacional.builder import ConstrutorDeTopico
from forum.criacional.factory_method import (
    CriadorDeAnexo,
    CriadorDeMensagem,
    CriadorDeTopico,
    obter_criador,
)
from forum.criacional.singleton import Forum
from forum.estrutural.composite import Anexo, Mensagem, Topico
from forum.estrutural.decorator import (
    ComAssinatura,
    ComCensura,
    ComDestaque,
    ConteudoSimples,
)
from forum.estrutural.facade import ForumFacade
from forum.modelos import Usuario


class BaseDeTeste(unittest.TestCase):
    """Silencia a saida do programa e garante um forum limpo por teste."""

    def setUp(self):
        Forum.resetar()
        self.saida = io.StringIO()
        self._contexto = redirect_stdout(self.saida)
        self._contexto.__enter__()
        self.ana = Usuario("ana", "ana@forum.com")
        self.bruno = Usuario("bruno", "bruno@forum.com", "moderador")

    def tearDown(self):
        self._contexto.__exit__(None, None, None)
        Forum.resetar()


class TesteSingleton(BaseDeTeste):
    def test_instancia_unica(self):
        self.assertIs(Forum(), Forum())

    def test_estado_compartilhado(self):
        Forum().registrar_usuario(self.ana)
        self.assertIsNotNone(Forum().obter_usuario("ana"))

    def test_contador_nao_reinicia(self):
        primeiro = Forum().proximo_identificador()
        segundo = Forum().proximo_identificador()
        self.assertEqual((primeiro, segundo), (1, 2))


class TesteFactoryMethod(BaseDeTeste):
    def test_cada_criador_devolve_seu_produto(self):
        topico = CriadorDeTopico().publicar(1, self.ana, titulo="T", conteudo="c")
        mensagem = CriadorDeMensagem().publicar(2, self.ana, conteudo="c")
        anexo = CriadorDeAnexo().publicar(3, self.ana, nome_arquivo="a.pdf", tamanho_kb=10)
        self.assertIsInstance(topico, Topico)
        self.assertIsInstance(mensagem, Mensagem)
        self.assertIsInstance(anexo, Anexo)

    def test_criador_por_nome(self):
        self.assertIsInstance(obter_criador("mensagem"), CriadorDeMensagem)

    def test_tipo_desconhecido(self):
        with self.assertRaises(ValueError):
            obter_criador("enquete")


class TesteBuilder(BaseDeTeste):
    def test_construcao_encadeada(self):
        topico = (
            ConstrutorDeTopico()
            .com_identificador(1)
            .com_autor(self.bruno)
            .com_titulo("Ordenacao")
            .com_conteudo("Qual algoritmo usar?")
            .com_tags(["python", "algoritmos", "python"])
            .fixado()
            .construir()
        )
        self.assertEqual(topico.titulo, "Ordenacao")
        self.assertEqual(topico.tags, ["python", "algoritmos"])
        self.assertTrue(topico.fixado)

    def test_builder_incompleto(self):
        construtor = ConstrutorDeTopico().com_identificador(1).com_titulo("X")
        with self.assertRaises(ValueError):
            construtor.construir()

    def test_reinicia_apos_construir(self):
        construtor = ConstrutorDeTopico()
        construtor.com_identificador(1).com_autor(self.ana).com_titulo("A").construir()
        with self.assertRaises(ValueError):
            construtor.construir()


class TesteComposite(BaseDeTeste):
    def montar_arvore(self):
        topico = Topico(1, self.ana, "Arvores", "Como percorrer?")
        resposta = topico.adicionar(Mensagem(2, self.bruno, "Use recursao."))
        resposta.adicionar(Mensagem(3, self.ana, "Entendi!"))
        resposta.adicionar(Anexo(4, self.bruno, "exemplo.py", 2))
        return topico, resposta

    def test_contagem_recursiva(self):
        topico, _ = self.montar_arvore()
        self.assertEqual(topico.total_itens(), 4)
        self.assertEqual(topico.total_respostas(), 2)

    def test_caminho_ate_a_raiz(self):
        topico, resposta = self.montar_arvore()
        self.assertEqual(resposta.filhos()[0].caminho(), "/T1/M2/M3")

    def test_folha_nao_aceita_filhos(self):
        anexo = Anexo(1, self.ana, "a.txt", 1)
        with self.assertRaises(TypeError):
            anexo.adicionar(Mensagem(2, self.ana, "x"))


class TesteDecorator(BaseDeTeste):
    def test_censura(self):
        texto = ComCensura(ConteudoSimples("Que lixo de resposta")).renderizar()
        self.assertEqual(texto, "Que **** de resposta")

    def test_pilha_de_decoradores(self):
        conteudo = ComAssinatura(
            ComDestaque(ComCensura(ConteudoSimples("isso e lixo"))), self.bruno
        )
        self.assertEqual(conteudo.renderizar(), ">>> isso e **** <<<\n-- bruno (moderador)")

    def test_ordem_importa(self):
        dentro = ComAssinatura(ComDestaque(ConteudoSimples("aviso")), self.bruno)
        fora = ComDestaque(ComAssinatura(ConteudoSimples("aviso"), self.bruno))
        self.assertEqual(dentro.renderizar(), ">>> aviso <<<\n-- bruno (moderador)")
        self.assertEqual(fora.renderizar(), ">>> aviso\n-- bruno (moderador) <<<")
        self.assertNotEqual(dentro.renderizar(), fora.renderizar())


class TesteObserver(BaseDeTeste):
    def test_notifica_inscritos(self):
        topico = Topico(1, self.ana, "Observer", "teste")
        topico.inscrever(NotificadorDeUsuario(self.ana))
        topico.inscrever(NotificadorDeUsuario(self.bruno))
        topico.notificar("nova-resposta", "mensagem publicada")
        self.assertEqual(len(self.ana.caixa_entrada), 1)
        self.assertEqual(len(self.bruno.caixa_entrada), 1)

    def test_nao_duplica_inscricao(self):
        topico = Topico(1, self.ana, "Observer", "teste")
        self.assertTrue(topico.inscrever(NotificadorDeUsuario(self.ana)))
        self.assertFalse(topico.inscrever(NotificadorDeUsuario(self.ana)))

    def test_desinscrever(self):
        topico = Topico(1, self.ana, "Observer", "teste")
        registro = RegistroDeAtividade()
        topico.inscrever(registro)
        topico.desinscrever(registro)
        topico.notificar("evento", "dados")
        self.assertEqual(registro.eventos, [])


class TesteStrategy(BaseDeTeste):
    def montar_topicos(self):
        primeiro = Topico(1, self.ana, "Primeiro", "a")
        segundo = Topico(2, self.ana, "Segundo", "b")
        primeiro.adicionar(Mensagem(3, self.bruno, "r1")).votar()
        primeiro.adicionar(Mensagem(4, self.bruno, "r2"))
        return [primeiro, segundo]

    def test_mais_recentes(self):
        ordem = PorMaisRecentes().ordenar(self.montar_topicos())
        self.assertEqual([t.identificador for t in ordem], [2, 1])

    def test_mais_respondidos(self):
        ordem = PorMaisRespondidos().ordenar(self.montar_topicos())
        self.assertEqual([t.identificador for t in ordem], [1, 2])

    def test_troca_em_execucao(self):
        topicos = self.montar_topicos()
        listagem = ListagemDeTopicos(PorMaisRecentes())
        self.assertEqual([t.identificador for t in listagem.listar(topicos)], [2, 1])
        listagem.definir_estrategia(PorMaisVotados())
        self.assertEqual([t.identificador for t in listagem.listar(topicos)], [1, 2])


class TesteState(BaseDeTeste):
    def test_estado_inicial(self):
        topico = Topico(1, self.ana, "State", "teste")
        self.assertIsInstance(topico.estado, Aberto)
        self.assertTrue(topico.aceita_resposta())

    def test_fechar_bloqueia_respostas(self):
        topico = Topico(1, self.ana, "State", "teste")
        self.assertTrue(topico.fechar())
        self.assertIsInstance(topico.estado, Fechado)
        self.assertFalse(topico.aceita_resposta())

    def test_arquivado_e_terminal(self):
        topico = Topico(1, self.ana, "State", "teste")
        topico.arquivar()
        self.assertIsInstance(topico.estado, Arquivado)
        self.assertFalse(topico.abrir())
        self.assertIsInstance(topico.estado, Arquivado)


class TesteFacade(BaseDeTeste):
    def setUp(self):
        super().setUp()
        self.fachada = ForumFacade()
        self.fachada.cadastrar_usuario("ana", "ana@forum.com")
        self.fachada.cadastrar_usuario("bruno", "bruno@forum.com", "moderador")

    def test_fluxo_completo(self):
        topico = self.fachada.abrir_discussao("ana", "Padroes", "Qual estudar?", ["gof"])
        self.assertIsNotNone(topico)
        self.fachada.inscrever(topico.identificador, "bruno")
        mensagem = self.fachada.responder(topico.identificador, "bruno", "Comece pelo Strategy.")
        self.assertIsNotNone(mensagem)
        self.assertEqual(topico.total_respostas(), 1)

    def test_topico_fechado_recusa_resposta(self):
        topico = self.fachada.abrir_discussao("ana", "Encerrado", "texto")
        self.fachada.alterar_estado(topico.identificador, "fechar")
        self.assertIsNone(self.fachada.responder(topico.identificador, "bruno", "oi"))

    def test_usuario_duplicado(self):
        self.assertIsNone(self.fachada.cadastrar_usuario("ana", "outro@forum.com"))

    def test_busca_recursiva(self):
        topico = self.fachada.abrir_discussao("ana", "Busca", "conteudo inicial")
        self.fachada.responder(topico.identificador, "bruno", "resposta com palavra rara")
        self.assertEqual(len(self.fachada.buscar("rara")), 1)

    def test_somente_moderador_fixa(self):
        self.assertIsNone(
            self.fachada.abrir_discussao("ana", "Aviso", "texto", fixado=True)
        )
        self.assertIsNotNone(
            self.fachada.abrir_discussao("bruno", "Aviso", "texto", fixado=True)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
