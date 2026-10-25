"""Demonstracao ponta a ponta da aplicacao em uso.

O roteiro sobe o servidor Flask em uma porta propria, executa o cenario
completo atraves dos endpoints (exatamente como o cliente faz) e imprime,
a cada passo, a requisicao, a resposta e o rastro de padroes devolvido
pelo servidor. No fim, abre a janela do cliente Qt ligada a esse servidor
e salva capturas de tela em docs/imagens/.

Uso (a partir da raiz do repositorio):

    python testes/demonstracao.py             # roteiro + capturas de tela
    python testes/demonstracao.py --sem-gui   # somente o roteiro HTTP

Em ambiente sem servidor grafico, use a plataforma offscreen do Qt:

    QT_QPA_PLATFORM=offscreen python testes/demonstracao.py
"""

import logging
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from werkzeug.serving import make_server  # noqa: E402

from cliente.api import ApiForum, ErroDaApi  # noqa: E402
from servidor.app import criar_app  # noqa: E402

PORTA = 5055
ENDERECO = f"http://127.0.0.1:{PORTA}"
PASTA_IMAGENS = RAIZ / "docs" / "imagens"


class ServidorEmSegundoPlano:
    """Sobe o app Flask em uma thread para o roteiro conversar com ele."""

    def __init__(self, porta=PORTA):
        # o log de acesso do werkzeug poluiria o roteiro impresso
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        self._servidor = make_server("127.0.0.1", porta, criar_app())
        self._thread = threading.Thread(target=self._servidor.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_erro):
        self._servidor.shutdown()
        self._thread.join(timeout=5)


def passo(numero, titulo):
    print(f"\n{'=' * 72}\nPASSO {numero} - {titulo}\n{'=' * 72}")


def mostrar(descricao, chamada):
    """Executa uma chamada da API e imprime resultado e rastro."""
    print(f"\n> {descricao}")
    try:
        resposta = chamada()
    except ErroDaApi as erro:
        print(f"  resposta: HTTP {erro.codigo} - {erro.mensagem}")
        for linha in erro.rastro:
            print(f"  rastro | {linha}")
        return None
    for linha in resposta.rastro:
        print(f"  rastro | {linha}")
    return resposta


def roteiro(api):
    passo(1, "Cadastro de usuarios")
    mostrar("POST /api/usuarios (ana, membro)",
            lambda: api.cadastrar_usuario("ana", "ana@forum.com"))
    mostrar("POST /api/usuarios (bruno, moderador)",
            lambda: api.cadastrar_usuario("bruno", "bruno@forum.com", "moderador"))
    mostrar("POST /api/usuarios (apelido repetido)",
            lambda: api.cadastrar_usuario("ana", "outro@forum.com"))

    passo(2, "Abertura de topicos (Builder + Factory Method)")
    mostrar("POST /api/topicos (ana)",
            lambda: api.abrir_topico("ana", "Como funciona a recursao em Python?",
                                     "Nao entendi o caso base.", ["python", "recursao"]))
    mostrar("POST /api/topicos (membro tentando fixar)",
            lambda: api.abrir_topico("ana", "Regras do forum", "Leia antes de postar.",
                                     ["avisos"], fixado=True))
    mostrar("POST /api/topicos (moderador fixando)",
            lambda: api.abrir_topico("bruno", "Regras do forum", "Leia antes de postar.",
                                     ["avisos"], fixado=True))

    passo(3, "Inscricao e resposta (Observer + State + Composite)")
    mostrar("POST /api/topicos/1/inscricoes (bruno)", lambda: api.inscrever(1, "bruno"))
    mostrar("POST /api/itens/1/respostas (bruno responde ao topico)",
            lambda: api.responder(1, "bruno", "Use um caso base para parar a recursao."))
    mostrar("POST /api/itens/3/respostas (ana responde a mensagem #3)",
            lambda: api.responder(3, "ana", "Obrigada! Funcionou aqui."))
    mostrar("POST /api/mensagens/4/anexos (folha da arvore)",
            lambda: api.anexar(4, "ana", "saida.txt", 2))

    passo(4, "Arvore da discussao (Composite serializado)")
    resposta = mostrar("GET /api/topicos/1", lambda: api.obter_topico(1))
    if resposta:
        print("\n  arvore recebida pelo cliente:")
        for linha in linhas_da_arvore(resposta.dados):
            print(f"  {linha}")

    passo(5, "Ordenacao da listagem (Strategy)")
    mostrar("POST /api/mensagens/3/votos", lambda: api.votar(3))
    mostrar("POST /api/mensagens/3/votos (segundo voto)", lambda: api.votar(3))
    for ordenacao in ("recentes", "votados"):
        resposta = mostrar(f"GET /api/topicos?ordenacao={ordenacao}",
                           lambda o=ordenacao: api.listar_topicos(o))
        if resposta:
            for posicao, topico in enumerate(resposta.dados, start=1):
                print(f"  {posicao}. {topico['rotulo']} "
                      f"(respostas: {topico['total_respostas']}, votos: {topico['total_votos']})")

    passo(6, "Ciclo de vida do topico (State)")
    mostrar("PUT /api/topicos/1/estado (fechar)", lambda: api.alterar_estado(1, "fechar"))
    mostrar("POST /api/itens/1/respostas (topico fechado)",
            lambda: api.responder(1, "ana", "Posso perguntar mais uma coisa?"))
    mostrar("PUT /api/topicos/1/estado (arquivar)", lambda: api.alterar_estado(1, "arquivar"))
    mostrar("PUT /api/topicos/1/estado (reabrir arquivado)",
            lambda: api.alterar_estado(1, "abrir"))

    passo(7, "Formatacao de conteudo (Decorator)")
    resposta = mostrar(
        "POST /api/conteudo/formatado (censura + destaque + assinatura)",
        lambda: api.formatar("Esse post e um lixo, autor burro.",
                             ["censura", "destaque", "assinatura"], "bruno"),
    )
    if resposta:
        print("\n  texto renderizado:")
        for linha in resposta.dados["texto"].split("\n"):
            print(f"  {linha}")

    passo(8, "Busca, notificacoes e estatisticas")
    resposta = mostrar('GET /api/busca?termo=recursao', lambda: api.buscar("recursao"))
    if resposta:
        for item in resposta.dados:
            print(f"  {item['caminho']} -> {item['rotulo']}")
    resposta = mostrar("GET /api/usuarios/ana/notificacoes", lambda: api.notificacoes("ana"))
    if resposta:
        for aviso in resposta.dados:
            print(f"  {aviso}")
    resposta = mostrar("GET /api/estatisticas", lambda: api.estatisticas())
    if resposta:
        for chave, valor in resposta.dados.items():
            print(f"  {chave} = {valor}")


def linhas_da_arvore(no, nivel=0):
    """Reconstroi no cliente a indentacao da arvore recebida em JSON."""
    linhas = ["   " * nivel + no["rotulo"]]
    for filho in no.get("filhos", []):
        linhas.extend(linhas_da_arvore(filho, nivel + 1))
    return linhas


def selecionar_topico(janela, identificador):
    """Seleciona na lista o topico com o identificador informado."""
    from PySide6.QtCore import Qt

    for posicao in range(janela.lista_topicos.count()):
        item = janela.lista_topicos.item(posicao)
        if item.data(Qt.ItemDataRole.UserRole)["identificador"] == identificador:
            janela.lista_topicos.setCurrentItem(item)
            return True
    return False


def capturar_tela(api):
    """Abre a janela do cliente e salva capturas em docs/imagens/."""
    from PySide6.QtWidgets import QApplication

    from cliente.dialogos import DialogoFormatar
    from cliente.janela import JanelaPrincipal

    PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)
    aplicacao = QApplication.instance() or QApplication([])

    janela = JanelaPrincipal(api)
    janela.resize(1180, 720)
    janela.show()
    selecionar_topico(janela, 1)
    aplicacao.processEvents()

    destino = PASTA_IMAGENS / "cliente-janela-principal.png"
    janela.grab().save(str(destino))
    print(f"\nCaptura salva: {destino.relative_to(RAIZ)}")

    dialogo = DialogoFormatar(janela)
    dialogo.texto.setPlainText("Esse post e um lixo, autor burro.")
    dialogo.censura.setChecked(True)
    dialogo.destaque.setChecked(True)
    dialogo.assinatura.setChecked(True)
    dialogo.mostrar_resultado(
        api.formatar("Esse post e um lixo, autor burro.",
                     ["censura", "destaque", "assinatura"], "bruno").dados["texto"]
    )
    aplicacao.processEvents()
    destino = PASTA_IMAGENS / "cliente-dialogo-formatar.png"
    dialogo.grab().save(str(destino))
    print(f"Captura salva: {destino.relative_to(RAIZ)}")

    dialogo.close()
    janela.close()


def main():
    com_gui = "--sem-gui" not in sys.argv
    with ServidorEmSegundoPlano():
        api = ApiForum(ENDERECO)
        print(f"Servidor de demonstracao em {ENDERECO}")
        roteiro(api)
        if com_gui:
            passo(9, "Cliente grafico em uso")
            capturar_tela(api)
    print("\nDemonstracao concluida.")


if __name__ == "__main__":
    main()
