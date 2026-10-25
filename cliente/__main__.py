"""Ponto de entrada do cliente grafico: python -m cliente [endereco]"""

import sys

from PySide6.QtWidgets import QApplication

from .api import ENDERECO_PADRAO, ApiForum
from .janela import JanelaPrincipal


def main(argumentos=None):
    argumentos = list(sys.argv[1:] if argumentos is None else argumentos)
    endereco = argumentos[0] if argumentos else ENDERECO_PADRAO

    aplicacao = QApplication(sys.argv[:1])
    janela = JanelaPrincipal(ApiForum(endereco))
    janela.show()
    return aplicacao.exec()


if __name__ == "__main__":
    sys.exit(main())
