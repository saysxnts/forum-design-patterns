"""Rastro de padroes acionados durante uma operacao.

O dominio nao imprime nada na tela: cada padrao registra aqui a linha que
descreve o que fez. O servidor limpa o rastro no inicio de cada requisicao
e devolve as linhas coletadas junto com a resposta, de modo que o cliente
grafico consegue mostrar, a cada acao, quais padroes entraram em cena.

Como o servidor Flask atende requisicoes em threads diferentes, o rastro e
guardado em armazenamento local de thread.
"""

import threading

_local = threading.local()


def iniciar():
    """Zera o rastro da thread atual. Chamado no inicio de cada requisicao."""
    _local.linhas = []


def rastrear(padrao, mensagem):
    """Registra uma linha de rastro e a devolve.

    `padrao` e o nome do padrao de projeto responsavel pela acao (ou None
    para linhas de apoio, como os passos internos do Builder).
    """
    linha = f"[{padrao}] {mensagem}" if padrao else mensagem
    linhas = getattr(_local, "linhas", None)
    if linhas is None:
        linhas = []
        _local.linhas = linhas
    linhas.append(linha)
    return linha


def linhas():
    """Devolve as linhas acumuladas sem apagar o rastro."""
    return list(getattr(_local, "linhas", []))


def coletar():
    """Devolve as linhas acumuladas e zera o rastro."""
    acumuladas = linhas()
    _local.linhas = []
    return acumuladas
