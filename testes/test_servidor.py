"""Testes do servidor Flask.

Cobrem o codigo das rotas (formato do envelope, status HTTP) e o
comportamento esperado da API (regras de negocio chegando ao cliente como
erro legivel). Cada teste roda sobre um forum limpo.
"""

import unittest

from forum import rastro
from forum.criacional.singleton import Forum
from forum.estrutural.facade import ForumFacade
from servidor.app import criar_app


class BaseDeTesteDoServidor(unittest.TestCase):
    def setUp(self):
        Forum.resetar()
        rastro.iniciar()
        self.app = criar_app(ForumFacade())
        self.app.config.update(TESTING=True)
        self.cliente = self.app.test_client()

    def tearDown(self):
        Forum.resetar()

    # apoio
    def criar_usuarios(self):
        self.cliente.post("/api/usuarios", json={"apelido": "ana", "email": "ana@forum.com"})
        self.cliente.post(
            "/api/usuarios",
            json={"apelido": "bruno", "email": "bruno@forum.com", "papel": "moderador"},
        )

    def criar_topico(self, autor="ana", titulo="Recursao", **extras):
        corpo = {"autor": autor, "titulo": titulo, "conteudo": "texto", **extras}
        return self.cliente.post("/api/topicos", json=corpo)

    def dados(self, resposta):
        return resposta.get_json()["dados"]


class TesteIndiceESaude(BaseDeTesteDoServidor):
    def test_indice_lista_endpoints(self):
        resposta = self.cliente.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(len(resposta.get_json()["endpoints"]) >= 10)

    def test_saude(self):
        resposta = self.cliente.get("/api/saude")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.dados(resposta), {"status": "ok"})

    def test_rota_inexistente(self):
        resposta = self.cliente.get("/api/inexistente")
        self.assertEqual(resposta.status_code, 404)
        self.assertIn("erro", resposta.get_json())

    def test_metodo_nao_permitido(self):
        resposta = self.cliente.delete("/api/usuarios")
        self.assertEqual(resposta.status_code, 405)


class TesteEnvelope(BaseDeTesteDoServidor):
    def test_resposta_traz_dados_e_rastro(self):
        resposta = self.cliente.post(
            "/api/usuarios", json={"apelido": "ana", "email": "ana@forum.com"}
        )
        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 201)
        self.assertIn("dados", corpo)
        self.assertIn("rastro", corpo)
        self.assertTrue(any("[Facade]" in linha for linha in corpo["rastro"]))

    def test_rastro_nao_vaza_entre_requisicoes(self):
        self.criar_usuarios()
        self.criar_topico()
        resposta = self.cliente.get("/api/saude")
        self.assertEqual(resposta.get_json()["rastro"], [])


class TesteUsuarios(BaseDeTesteDoServidor):
    def test_cadastro_e_listagem(self):
        self.criar_usuarios()
        resposta = self.cliente.get("/api/usuarios")
        apelidos = [u["apelido"] for u in self.dados(resposta)]
        self.assertEqual(apelidos, ["ana", "bruno"])

    def test_apelido_duplicado(self):
        self.criar_usuarios()
        resposta = self.cliente.post(
            "/api/usuarios", json={"apelido": "ana", "email": "x@forum.com"}
        )
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("ana", resposta.get_json()["erro"])

    def test_apelido_vazio(self):
        resposta = self.cliente.post("/api/usuarios", json={"apelido": "", "email": "x@x.com"})
        self.assertEqual(resposta.status_code, 400)

    def test_papel_invalido(self):
        resposta = self.cliente.post(
            "/api/usuarios", json={"apelido": "ana", "email": "a@a.com", "papel": "admin"}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_notificacoes_de_usuario_inexistente(self):
        self.assertEqual(self.cliente.get("/api/usuarios/zeca/notificacoes").status_code, 404)


class TesteTopicos(BaseDeTesteDoServidor):
    def setUp(self):
        super().setUp()
        self.criar_usuarios()

    def test_abertura_devolve_arvore(self):
        resposta = self.criar_topico(tags=["python"])
        dados = self.dados(resposta)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(dados["tipo"], "topico")
        self.assertEqual(dados["estado"], "Aberto")
        self.assertEqual(dados["filhos"], [])
        self.assertEqual(dados["inscritos"], ["ana"])

    def test_autor_inexistente(self):
        self.assertEqual(self.criar_topico(autor="zeca").status_code, 404)

    def test_titulo_vazio(self):
        self.assertEqual(self.criar_topico(titulo="   ").status_code, 400)

    def test_membro_nao_fixa(self):
        self.assertEqual(self.criar_topico(autor="ana", fixado=True).status_code, 403)

    def test_moderador_fixa(self):
        resposta = self.criar_topico(autor="bruno", fixado=True)
        self.assertTrue(self.dados(resposta)["fixado"])

    def test_topico_inexistente(self):
        self.assertEqual(self.cliente.get("/api/topicos/99").status_code, 404)

    def test_ordenacao_invalida(self):
        resposta = self.cliente.get("/api/topicos?ordenacao=alfabetica")
        self.assertEqual(resposta.status_code, 400)

    def test_ordenacao_por_votos(self):
        self.criar_topico(titulo="Primeiro")
        self.criar_topico(titulo="Segundo")
        self.cliente.post("/api/itens/1/respostas", json={"autor": "ana", "conteudo": "oi"})
        self.cliente.post("/api/mensagens/3/votos")

        recentes = self.dados(self.cliente.get("/api/topicos?ordenacao=recentes"))
        votados = self.dados(self.cliente.get("/api/topicos?ordenacao=votados"))
        self.assertEqual([t["identificador"] for t in recentes], [2, 1])
        self.assertEqual([t["identificador"] for t in votados], [1, 2])


class TesteRespostasEAnexos(BaseDeTesteDoServidor):
    def setUp(self):
        super().setUp()
        self.criar_usuarios()
        self.criar_topico()

    def test_resposta_aninhada(self):
        self.cliente.post("/api/itens/1/respostas", json={"autor": "bruno", "conteudo": "r1"})
        self.cliente.post("/api/itens/2/respostas", json={"autor": "ana", "conteudo": "r2"})
        arvore = self.dados(self.cliente.get("/api/topicos/1"))
        self.assertEqual(arvore["filhos"][0]["filhos"][0]["conteudo"], "r2")
        self.assertEqual(arvore["total_itens"], 3)

    def test_resposta_vazia(self):
        resposta = self.cliente.post(
            "/api/itens/1/respostas", json={"autor": "ana", "conteudo": "   "}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_resposta_a_item_inexistente(self):
        resposta = self.cliente.post(
            "/api/itens/77/respostas", json={"autor": "ana", "conteudo": "oi"}
        )
        self.assertEqual(resposta.status_code, 404)

    def test_anexo_em_mensagem(self):
        self.cliente.post("/api/itens/1/respostas", json={"autor": "ana", "conteudo": "r"})
        resposta = self.cliente.post(
            "/api/mensagens/2/anexos",
            json={"autor": "ana", "nome_arquivo": "saida.txt", "tamanho_kb": 2},
        )
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(self.dados(resposta)["caminho"], "/T1/M2/A3")

    def test_anexo_em_anexo_e_recusado(self):
        self.cliente.post("/api/itens/1/respostas", json={"autor": "ana", "conteudo": "r"})
        self.cliente.post(
            "/api/mensagens/2/anexos", json={"autor": "ana", "nome_arquivo": "a.txt"}
        )
        resposta = self.cliente.post(
            "/api/mensagens/3/anexos", json={"autor": "ana", "nome_arquivo": "b.txt"}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_voto_em_topico_e_recusado(self):
        self.assertEqual(self.cliente.post("/api/mensagens/1/votos").status_code, 400)


class TesteEstadoEObserver(BaseDeTesteDoServidor):
    def setUp(self):
        super().setUp()
        self.criar_usuarios()
        self.criar_topico()

    def test_inscricao_e_notificacao(self):
        self.cliente.post("/api/topicos/1/inscricoes", json={"apelido": "bruno"})
        self.cliente.post("/api/itens/1/respostas", json={"autor": "bruno", "conteudo": "oi"})
        avisos = self.dados(self.cliente.get("/api/usuarios/ana/notificacoes"))
        self.assertEqual(len(avisos), 1)
        self.assertIn("nova-resposta", avisos[0])

    def test_inscricao_duplicada(self):
        self.cliente.post("/api/topicos/1/inscricoes", json={"apelido": "bruno"})
        resposta = self.cliente.post("/api/topicos/1/inscricoes", json={"apelido": "bruno"})
        self.assertEqual(resposta.status_code, 409)

    def test_fechar_bloqueia_resposta(self):
        self.cliente.put("/api/topicos/1/estado", json={"acao": "fechar"})
        resposta = self.cliente.post(
            "/api/itens/1/respostas", json={"autor": "ana", "conteudo": "oi"}
        )
        self.assertEqual(resposta.status_code, 409)

    def test_arquivado_nao_reabre(self):
        self.cliente.put("/api/topicos/1/estado", json={"acao": "arquivar"})
        resposta = self.cliente.put("/api/topicos/1/estado", json={"acao": "abrir"})
        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(
            self.dados(self.cliente.get("/api/topicos/1"))["estado"], "Arquivado"
        )

    def test_acao_de_estado_invalida(self):
        resposta = self.cliente.put("/api/topicos/1/estado", json={"acao": "trancar"})
        self.assertEqual(resposta.status_code, 400)


class TesteConteudoEConsultas(BaseDeTesteDoServidor):
    def setUp(self):
        super().setUp()
        self.criar_usuarios()
        self.criar_topico(titulo="Recursao em Python")

    def test_formatacao_com_pilha_de_filtros(self):
        resposta = self.cliente.post(
            "/api/conteudo/formatado",
            json={
                "texto": "isso e lixo",
                "filtros": ["censura", "destaque", "assinatura"],
                "autor": "bruno",
            },
        )
        self.assertEqual(
            self.dados(resposta)["texto"], ">>> isso e **** <<<\n-- bruno (moderador)"
        )

    def test_filtro_desconhecido(self):
        resposta = self.cliente.post(
            "/api/conteudo/formatado", json={"texto": "oi", "filtros": ["negrito"]}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_busca_encontra_na_arvore(self):
        self.cliente.post(
            "/api/itens/1/respostas", json={"autor": "ana", "conteudo": "palavra rara"}
        )
        encontrados = self.dados(self.cliente.get("/api/busca?termo=rara"))
        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0]["caminho"], "/T1/M2")

    def test_busca_sem_termo(self):
        self.assertEqual(self.cliente.get("/api/busca?termo=").status_code, 400)

    def test_estatisticas(self):
        dados = self.dados(self.cliente.get("/api/estatisticas"))
        self.assertTrue(dados["instancia_unica"])
        self.assertEqual(dados["usuarios"], 2)
        self.assertEqual(dados["topicos"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
