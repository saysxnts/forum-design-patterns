"""Servidor Flask do forum de discussao.

Cada endpoint e uma casca fina: valida a entrada, chama um metodo da
fachada do dominio (forum.estrutural.facade.ForumFacade) e devolve JSON.
Nenhuma rota conhece as classes dos padroes de projeto, e o dominio nao
importa nada do Flask.

Toda resposta tem o mesmo envelope:

    {
      "dados":  <resultado da operacao>,
      "rastro": ["[Builder] ...", "[Factory Method] ...", ...]
    }

O campo "rastro" traz os padroes acionados naquela requisicao. O cliente
grafico mostra essas linhas em um painel lateral, o que torna o
funcionamento dos padroes visivel durante a demonstracao.

Execucao:
    python -m servidor
"""

from flask import Flask, jsonify, request

from forum import rastro
from forum.erros import ErroDeForum
from forum.estrutural.facade import ForumFacade

ENDPOINTS = [
    ("GET", "/api/saude", "Estado do servidor"),
    ("GET", "/api/usuarios", "Lista os usuarios cadastrados"),
    ("POST", "/api/usuarios", "Cadastra um usuario"),
    ("GET", "/api/usuarios/<apelido>/notificacoes", "Caixa de entrada do usuario (Observer)"),
    ("GET", "/api/topicos", "Lista topicos; ?ordenacao=recentes|respondidos|votados (Strategy)"),
    ("POST", "/api/topicos", "Abre um topico (Builder + Factory Method)"),
    ("GET", "/api/topicos/<id>", "Arvore completa da discussao (Composite)"),
    ("POST", "/api/topicos/<id>/inscricoes", "Inscreve um usuario no topico (Observer)"),
    ("PUT", "/api/topicos/<id>/estado", "Abre, fecha ou arquiva o topico (State)"),
    ("POST", "/api/itens/<id>/respostas", "Responde a um topico ou a uma mensagem"),
    ("POST", "/api/mensagens/<id>/anexos", "Anexa um arquivo a uma mensagem (Composite)"),
    ("POST", "/api/mensagens/<id>/votos", "Registra um voto na mensagem"),
    ("POST", "/api/conteudo/formatado", "Aplica a pilha de filtros ao texto (Decorator)"),
    ("GET", "/api/busca", "Busca por texto em todas as arvores; ?termo="),
    ("GET", "/api/estatisticas", "Numeros do forum (Singleton)"),
]


def resumo_de_topico(topico):
    """Versao curta de um topico, usada nas listagens."""
    return {
        "identificador": topico.identificador,
        "titulo": topico.titulo,
        "autor": topico.autor.apelido,
        "estado": topico.estado.nome,
        "fixado": topico.fixado,
        "tags": list(topico.tags),
        "total_respostas": topico.total_respostas(),
        "total_votos": topico.total_votos(),
        "aceita_resposta": topico.aceita_resposta(),
        "rotulo": topico.rotulo(),
        "caminho": topico.caminho(),
    }


def resumo_de_item(item):
    """Versao curta de qualquer no da arvore, usada na busca."""
    return {
        "identificador": item.identificador,
        "tipo": item.tipo,
        "caminho": item.caminho(),
        "rotulo": item.rotulo(),
        "autor": item.autor.apelido,
        "topico": item.raiz().identificador,
    }


def criar_app(fachada=None):
    """Monta a aplicacao Flask.

    Receber a fachada por parametro mantem o servidor testavel: os testes
    passam uma fachada sobre um forum limpo.
    """
    app = Flask(__name__)
    app.json.ensure_ascii = False
    servico = fachada or ForumFacade()
    app.extensions["fachada"] = servico

    # --- envelope de resposta ----------------------------------------------
    def responder(dados, status=200):
        linhas = rastro.coletar()
        for linha in linhas:
            app.logger.info(linha)
        return jsonify({"dados": dados, "rastro": linhas}), status

    def corpo():
        return request.get_json(silent=True) or {}

    @app.before_request
    def preparar_rastro():
        rastro.iniciar()

    @app.errorhandler(ErroDeForum)
    def tratar_erro_de_dominio(erro):
        return jsonify(
            {"erro": erro.mensagem, "rastro": rastro.coletar()}
        ), erro.codigo

    @app.errorhandler(404)
    def tratar_rota_inexistente(_erro):
        return jsonify({"erro": "Endpoint nao encontrado."}), 404

    @app.errorhandler(405)
    def tratar_metodo_invalido(_erro):
        return jsonify({"erro": "Metodo nao permitido para este endpoint."}), 405

    # --- raiz e saude -------------------------------------------------------
    @app.get("/")
    def indice():
        return jsonify(
            {
                "aplicacao": "Forum de Discussao - projeto de Design Patterns",
                "endpoints": [
                    {"metodo": m, "rota": r, "descricao": d} for m, r, d in ENDPOINTS
                ],
            }
        )

    @app.get("/api/saude")
    def saude():
        return responder({"status": "ok"})

    # --- usuarios -----------------------------------------------------------
    @app.get("/api/usuarios")
    def listar_usuarios():
        usuarios = [
            {"apelido": u.apelido, "email": u.email, "papel": u.papel}
            for u in servico.listar_usuarios()
        ]
        return responder(usuarios)

    @app.post("/api/usuarios")
    def cadastrar_usuario():
        dados = corpo()
        usuario = servico.cadastrar_usuario(
            dados.get("apelido"), dados.get("email"), dados.get("papel", "membro")
        )
        return responder(
            {"apelido": usuario.apelido, "email": usuario.email, "papel": usuario.papel},
            201,
        )

    @app.get("/api/usuarios/<apelido>/notificacoes")
    def notificacoes(apelido):
        return responder(servico.caixa_de_entrada(apelido))

    # --- topicos ------------------------------------------------------------
    @app.get("/api/topicos")
    def listar_topicos():
        ordenacao = request.args.get("ordenacao")
        topicos = servico.listar_topicos(ordenacao)
        return responder([resumo_de_topico(t) for t in topicos])

    @app.post("/api/topicos")
    def abrir_topico():
        dados = corpo()
        topico = servico.abrir_discussao(
            dados.get("autor"),
            dados.get("titulo"),
            dados.get("conteudo", ""),
            dados.get("tags"),
            bool(dados.get("fixado", False)),
        )
        return responder(topico.para_dicionario(), 201)

    @app.get("/api/topicos/<int:identificador>")
    def obter_topico(identificador):
        topico = servico.obter_topico(identificador)
        return responder(topico.para_dicionario())

    @app.post("/api/topicos/<int:identificador>/inscricoes")
    def inscrever(identificador):
        topico = servico.inscrever(identificador, corpo().get("apelido"))
        return responder(resumo_de_topico(topico), 201)

    @app.put("/api/topicos/<int:identificador>/estado")
    def alterar_estado(identificador):
        topico = servico.alterar_estado(identificador, corpo().get("acao"))
        return responder(resumo_de_topico(topico))

    # --- mensagens e anexos -------------------------------------------------
    @app.post("/api/itens/<int:identificador>/respostas")
    def responder_item(identificador):
        dados = corpo()
        mensagem = servico.responder(identificador, dados.get("autor"), dados.get("conteudo"))
        return responder(mensagem.para_dicionario(), 201)

    @app.post("/api/mensagens/<int:identificador>/anexos")
    def anexar(identificador):
        dados = corpo()
        anexo = servico.anexar(
            identificador,
            dados.get("autor"),
            dados.get("nome_arquivo"),
            dados.get("tamanho_kb", 0),
        )
        return responder(anexo.para_dicionario(), 201)

    @app.post("/api/mensagens/<int:identificador>/votos")
    def votar(identificador):
        mensagem = servico.votar(identificador)
        return responder(mensagem.para_dicionario())

    # --- conteudo, busca e estatisticas -------------------------------------
    @app.post("/api/conteudo/formatado")
    def formatar():
        dados = corpo()
        texto = servico.formatar(
            dados.get("texto"), dados.get("filtros") or [], dados.get("autor")
        )
        return responder({"texto": texto})

    @app.get("/api/busca")
    def buscar():
        encontrados = servico.buscar(request.args.get("termo"))
        return responder([resumo_de_item(item) for item in encontrados])

    @app.get("/api/estatisticas")
    def estatisticas():
        return responder(servico.estatisticas())

    return app


if __name__ == "__main__":
    criar_app().run(host="127.0.0.1", port=5000, debug=False)
