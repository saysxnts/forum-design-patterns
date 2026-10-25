"""Testes da camada de acesso do cliente (ApiForum).

O proxy do cliente e exercitado contra o servidor real, sem rede: uma
sessao de teste encaminha cada chamada para o test_client do Flask. Alem
do caminho feliz, os testes cobrem a traducao de erro HTTP em ErroDaApi,
a falha de conexao e a resposta que nao e JSON.
"""

import json
import unittest

import requests

from cliente.api import ApiForum, ErroDaApi
from forum import rastro
from forum.criacional.singleton import Forum
from forum.estrutural.facade import ForumFacade
from servidor.app import criar_app

ENDERECO = "http://servidor-de-teste"


class RespostaDeTeste:
    """Adapta a resposta do Flask a interface que o ApiForum espera."""

    def __init__(self, resposta):
        self.status_code = resposta.status_code
        self._texto = resposta.get_data(as_text=True)

    def json(self):
        return json.loads(self._texto)


class SessaoDeTeste:
    """Encaminha as requisicoes do cliente para o test_client do Flask."""

    def __init__(self, cliente_flask):
        self._cliente = cliente_flask
        self.chamadas = []

    def request(self, metodo, url, timeout=None, json=None, params=None):
        caminho = url[len(ENDERECO):]
        self.chamadas.append((metodo, caminho))
        resposta = self._cliente.open(
            caminho, method=metodo, json=json, query_string=params
        )
        return RespostaDeTeste(resposta)


class SessaoQueFalha:
    def request(self, *_args, **_kwargs):
        raise requests.ConnectionError("conexao recusada")


class SessaoSemJson:
    class _Resposta:
        status_code = 200

        def json(self):
            raise ValueError("nao e json")

    def request(self, *_args, **_kwargs):
        return self._Resposta()


class BaseDeTesteDoCliente(unittest.TestCase):
    def setUp(self):
        Forum.resetar()
        rastro.iniciar()
        app = criar_app(ForumFacade())
        app.config.update(TESTING=True)
        self.sessao = SessaoDeTeste(app.test_client())
        self.api = ApiForum(ENDERECO, sessao=self.sessao)

    def tearDown(self):
        Forum.resetar()


class TesteTransporte(BaseDeTesteDoCliente):
    def test_endereco_sem_barra_final(self):
        self.assertEqual(ApiForum("http://host:5000/").endereco, "http://host:5000")

    def test_monta_a_rota_correta(self):
        self.api.saude()
        self.assertEqual(self.sessao.chamadas[-1], ("GET", "/api/saude"))

    def test_resposta_traz_dados_e_rastro(self):
        resposta = self.api.cadastrar_usuario("ana", "ana@forum.com")
        self.assertEqual(resposta.dados["apelido"], "ana")
        self.assertTrue(resposta.rastro)

    def test_erro_http_vira_excecao(self):
        self.api.cadastrar_usuario("ana", "ana@forum.com")
        with self.assertRaises(ErroDaApi) as contexto:
            self.api.cadastrar_usuario("ana", "outro@forum.com")
        self.assertEqual(contexto.exception.codigo, 409)
        self.assertIn("ana", contexto.exception.mensagem)

    def test_servidor_fora_do_ar(self):
        api = ApiForum(ENDERECO, sessao=SessaoQueFalha())
        with self.assertRaises(ErroDaApi) as contexto:
            api.saude()
        self.assertIn("servidor", contexto.exception.mensagem.lower())
        self.assertIsNone(contexto.exception.codigo)

    def test_resposta_que_nao_e_json(self):
        api = ApiForum(ENDERECO, sessao=SessaoSemJson())
        with self.assertRaises(ErroDaApi):
            api.saude()


class TesteOperacoes(BaseDeTesteDoCliente):
    def setUp(self):
        super().setUp()
        self.api.cadastrar_usuario("ana", "ana@forum.com")
        self.api.cadastrar_usuario("bruno", "bruno@forum.com", "moderador")

    def test_fluxo_de_discussao(self):
        topico = self.api.abrir_topico("ana", "Recursao", "duvida", ["python"]).dados
        self.api.inscrever(topico["identificador"], "bruno")
        mensagem = self.api.responder(topico["identificador"], "bruno", "use caso base").dados
        self.api.anexar(mensagem["identificador"], "bruno", "exemplo.py", 3)

        arvore = self.api.obter_topico(topico["identificador"]).dados
        self.assertEqual(arvore["total_itens"], 3)
        self.assertEqual(arvore["filhos"][0]["filhos"][0]["tipo"], "anexo")
        self.assertEqual(sorted(arvore["inscritos"]), ["ana", "bruno"])

    def test_listagem_com_ordenacao(self):
        self.api.abrir_topico("ana", "Primeiro", "a")
        self.api.abrir_topico("ana", "Segundo", "b")
        self.api.listar_topicos("recentes")
        self.assertEqual(self.sessao.chamadas[-1], ("GET", "/api/topicos"))
        topicos = self.api.listar_topicos("recentes").dados
        self.assertEqual([t["titulo"] for t in topicos], ["Segundo", "Primeiro"])

    def test_estado_e_recusa_de_resposta(self):
        topico = self.api.abrir_topico("ana", "Encerrado", "a").dados
        self.api.alterar_estado(topico["identificador"], "fechar")
        with self.assertRaises(ErroDaApi) as contexto:
            self.api.responder(topico["identificador"], "ana", "oi")
        self.assertEqual(contexto.exception.codigo, 409)

    def test_formatacao(self):
        texto = self.api.formatar("isso e lixo", ["censura"], "bruno").dados["texto"]
        self.assertEqual(texto, "isso e ****")

    def test_notificacoes_e_estatisticas(self):
        topico = self.api.abrir_topico("ana", "Observer", "a").dados
        self.api.responder(topico["identificador"], "ana", "resposta")
        self.assertEqual(len(self.api.notificacoes("ana").dados), 1)
        self.assertTrue(self.api.estatisticas().dados["instancia_unica"])

    def test_busca(self):
        self.api.abrir_topico("ana", "Padroes de projeto", "conteudo")
        encontrados = self.api.buscar("padroes").dados
        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0]["tipo"], "topico")


if __name__ == "__main__":
    unittest.main(verbosity=2)
