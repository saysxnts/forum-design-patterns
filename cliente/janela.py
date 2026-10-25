"""Janela principal do cliente grafico (PySide6).

A janela nao conhece o dominio: todas as operacoes passam por ApiForum, o
proxy que fala com os endpoints do servidor. Cada resposta traz o rastro
dos padroes acionados, exibido no painel "Padroes em acao" a direita.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .api import ErroDaApi
from .dialogos import (
    DialogoAnexo,
    DialogoFormatar,
    DialogoNovoTopico,
    DialogoResposta,
    DialogoUsuario,
)

ORDENACOES = [
    ("Mais recentes", "recentes"),
    ("Mais respondidos", "respondidos"),
    ("Mais votados", "votados"),
]

ACOES_DE_ESTADO = [("Abrir", "abrir"), ("Fechar", "fechar"), ("Arquivar", "arquivar")]


class JanelaPrincipal(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self._topico_atual = None
        self.setWindowTitle("Forum de Discussao - cliente Qt")
        self.resize(1180, 720)
        self._montar_interface()
        self._montar_menu()
        self.recarregar_tudo()

    # ------------------------------------------------------------------ UI --
    def _montar_interface(self):
        central = QWidget()
        principal = QVBoxLayout(central)

        # barra superior: usuario atual, ordenacao e busca
        barra = QHBoxLayout()
        barra.addWidget(QLabel("Usuario atual:"))
        self.combo_usuario = QComboBox()
        self.combo_usuario.setMinimumWidth(170)
        barra.addWidget(self.combo_usuario)

        self.botao_novo_usuario = QPushButton("Cadastrar usuario")
        self.botao_novo_usuario.clicked.connect(self.cadastrar_usuario)
        barra.addWidget(self.botao_novo_usuario)

        barra.addSpacing(18)
        barra.addWidget(QLabel("Ordenar por:"))
        self.combo_ordenacao = QComboBox()
        for rotulo, chave in ORDENACOES:
            self.combo_ordenacao.addItem(rotulo, chave)
        self.combo_ordenacao.currentIndexChanged.connect(self.carregar_topicos)
        barra.addWidget(self.combo_ordenacao)

        barra.addStretch()
        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("buscar por texto...")
        self.campo_busca.setMinimumWidth(200)
        self.campo_busca.returnPressed.connect(self.buscar)
        barra.addWidget(self.campo_busca)
        self.botao_busca = QPushButton("Buscar")
        self.botao_busca.clicked.connect(self.buscar)
        barra.addWidget(self.botao_busca)
        principal.addLayout(barra)

        divisor = QSplitter(Qt.Orientation.Horizontal)

        # coluna 1: topicos
        coluna_topicos = QWidget()
        layout_topicos = QVBoxLayout(coluna_topicos)
        layout_topicos.addWidget(QLabel("Topicos"))
        self.lista_topicos = QListWidget()
        self.lista_topicos.currentItemChanged.connect(self._mudou_topico)
        layout_topicos.addWidget(self.lista_topicos)

        self.botao_novo_topico = QPushButton("Abrir novo topico")
        self.botao_novo_topico.clicked.connect(self.abrir_topico)
        layout_topicos.addWidget(self.botao_novo_topico)

        self.botao_inscrever = QPushButton("Inscrever usuario atual")
        self.botao_inscrever.clicked.connect(self.inscrever)
        layout_topicos.addWidget(self.botao_inscrever)

        linha_estado = QHBoxLayout()
        self.combo_estado = QComboBox()
        for rotulo, chave in ACOES_DE_ESTADO:
            self.combo_estado.addItem(rotulo, chave)
        linha_estado.addWidget(self.combo_estado)
        self.botao_estado = QPushButton("Aplicar")
        self.botao_estado.clicked.connect(self.alterar_estado)
        linha_estado.addWidget(self.botao_estado)
        layout_topicos.addLayout(linha_estado)
        divisor.addWidget(coluna_topicos)

        # coluna 2: arvore da discussao
        coluna_arvore = QWidget()
        layout_arvore = QVBoxLayout(coluna_arvore)
        self.rotulo_discussao = QLabel("Discussao")
        layout_arvore.addWidget(self.rotulo_discussao)
        self.arvore = QTreeWidget()
        self.arvore.setHeaderLabels(["Item", "Autor", "Votos"])
        self.arvore.setColumnWidth(0, 330)
        self.arvore.setColumnWidth(1, 90)
        self.arvore.header().setStretchLastSection(True)
        layout_arvore.addWidget(self.arvore)

        linha_acoes = QHBoxLayout()
        self.botao_responder = QPushButton("Responder")
        self.botao_responder.clicked.connect(self.responder)
        self.botao_anexar = QPushButton("Anexar arquivo")
        self.botao_anexar.clicked.connect(self.anexar)
        self.botao_votar = QPushButton("Votar")
        self.botao_votar.clicked.connect(self.votar)
        for botao in (self.botao_responder, self.botao_anexar, self.botao_votar):
            linha_acoes.addWidget(botao)
        layout_arvore.addLayout(linha_acoes)
        divisor.addWidget(coluna_arvore)

        # coluna 3: rastro dos padroes
        coluna_rastro = QWidget()
        layout_rastro = QVBoxLayout(coluna_rastro)
        layout_rastro.addWidget(QLabel("Padroes em acao"))
        self.painel_rastro = QPlainTextEdit()
        self.painel_rastro.setReadOnly(True)
        layout_rastro.addWidget(self.painel_rastro)
        self.botao_limpar = QPushButton("Limpar painel")
        self.botao_limpar.clicked.connect(self.painel_rastro.clear)
        layout_rastro.addWidget(self.botao_limpar)
        divisor.addWidget(coluna_rastro)

        divisor.setSizes([290, 540, 350])
        principal.addWidget(divisor)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto.")

    def _montar_menu(self):
        menu_forum = self.menuBar().addMenu("&Forum")
        menu_forum.addAction("Atualizar", self.recarregar_tudo)
        menu_forum.addAction("Estatisticas", self.mostrar_estatisticas)
        menu_forum.addAction("Notificacoes do usuario atual", self.mostrar_notificacoes)
        menu_forum.addSeparator()
        menu_forum.addAction("Sair", self.close)

        menu_conteudo = self.menuBar().addMenu("&Conteudo")
        menu_conteudo.addAction("Formatar texto...", self.formatar_conteudo)

        menu_ajuda = self.menuBar().addMenu("&Ajuda")
        menu_ajuda.addAction("Sobre", self.mostrar_sobre)

    # -------------------------------------------------------------- apoio --
    @property
    def usuario_atual(self):
        return self.combo_usuario.currentText() or None

    def _executar(self, descricao, chamada):
        """Chama a API, trata o erro e registra o rastro no painel."""
        try:
            resposta = chamada()
        except ErroDaApi as erro:
            self._registrar(descricao, erro.rastro, falhou=True)
            QMessageBox.warning(self, "Nao foi possivel concluir", erro.mensagem)
            self.statusBar().showMessage(f"{descricao}: {erro.mensagem}", 8000)
            return None
        self._registrar(descricao, resposta.rastro)
        self.statusBar().showMessage(f"{descricao}: concluido.", 5000)
        return resposta

    def _registrar(self, descricao, rastro, falhou=False):
        marca = "FALHOU" if falhou else "OK"
        self.painel_rastro.appendPlainText(f"--- {descricao} [{marca}] ---")
        for linha in rastro or []:
            self.painel_rastro.appendPlainText(linha)
        if not rastro:
            self.painel_rastro.appendPlainText("(nenhum padrao acionado)")
        self.painel_rastro.appendPlainText("")

    def _exigir_usuario(self):
        if not self.usuario_atual:
            QMessageBox.information(
                self, "Sem usuario", "Cadastre e selecione um usuario antes desta acao."
            )
            return None
        return self.usuario_atual

    def _exigir_topico(self):
        if self._topico_atual is None:
            QMessageBox.information(self, "Sem topico", "Selecione um topico na lista.")
            return None
        return self._topico_atual

    def _item_selecionado(self):
        item = self.arvore.currentItem()
        if item is None:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    # ------------------------------------------------------------ carregar --
    def recarregar_tudo(self):
        self.carregar_usuarios()
        self.carregar_topicos()

    def carregar_usuarios(self):
        resposta = self._executar("Listar usuarios", self.api.listar_usuarios)
        if resposta is None:
            return
        atual = self.usuario_atual
        self.combo_usuario.clear()
        for usuario in resposta.dados:
            self.combo_usuario.addItem(usuario["apelido"], usuario)
        if atual:
            posicao = self.combo_usuario.findText(atual)
            if posicao >= 0:
                self.combo_usuario.setCurrentIndex(posicao)

    def carregar_topicos(self):
        ordenacao = self.combo_ordenacao.currentData()
        resposta = self._executar(
            f"Listar topicos ({ordenacao})", lambda: self.api.listar_topicos(ordenacao)
        )
        if resposta is None:
            return
        selecionado = self._topico_atual
        self.lista_topicos.clear()
        for topico in resposta.dados:
            item = QListWidgetItem(topico["rotulo"])
            item.setData(Qt.ItemDataRole.UserRole, topico)
            self.lista_topicos.addItem(item)
            if topico["identificador"] == selecionado:
                self.lista_topicos.setCurrentItem(item)

    def _mudou_topico(self, atual, _anterior=None):
        if atual is None:
            self._topico_atual = None
            self.arvore.clear()
            return
        self._topico_atual = atual.data(Qt.ItemDataRole.UserRole)["identificador"]
        self.carregar_discussao()

    def carregar_discussao(self):
        if self._topico_atual is None:
            return
        resposta = self._executar(
            f"Abrir discussao #{self._topico_atual}",
            lambda: self.api.obter_topico(self._topico_atual),
        )
        if resposta is None:
            return
        topico = resposta.dados
        self.rotulo_discussao.setText(
            f"{topico['titulo']} - {topico['estado']} - "
            f"{topico['total_respostas']} resposta(s), {topico['total_votos']} voto(s)"
        )
        self.arvore.clear()
        raiz = self._montar_no(topico)
        self.arvore.addTopLevelItem(raiz)
        self.arvore.expandAll()
        self.arvore.setCurrentItem(raiz)

    def _montar_no(self, dados):
        item = QTreeWidgetItem(
            [dados["rotulo"], dados["autor"], str(dados.get("votos", ""))]
        )
        item.setData(0, Qt.ItemDataRole.UserRole, dados)
        for filho in dados.get("filhos", []):
            item.addChild(self._montar_no(filho))
        return item

    # --------------------------------------------------------------- acoes --
    def cadastrar_usuario(self):
        dialogo = DialogoUsuario(self)
        if dialogo.exec() != DialogoUsuario.DialogCode.Accepted:
            return
        valores = dialogo.valores()
        resposta = self._executar(
            "Cadastrar usuario",
            lambda: self.api.cadastrar_usuario(
                valores["apelido"], valores["email"], valores["papel"]
            ),
        )
        if resposta is None:
            return
        self.carregar_usuarios()
        posicao = self.combo_usuario.findText(resposta.dados["apelido"])
        if posicao >= 0:
            self.combo_usuario.setCurrentIndex(posicao)

    def abrir_topico(self):
        autor = self._exigir_usuario()
        if autor is None:
            return
        dados_usuario = self.combo_usuario.currentData() or {}
        dialogo = DialogoNovoTopico(self, pode_fixar=dados_usuario.get("papel") == "moderador")
        if dialogo.exec() != DialogoNovoTopico.DialogCode.Accepted:
            return
        valores = dialogo.valores()
        resposta = self._executar(
            "Abrir topico",
            lambda: self.api.abrir_topico(
                autor, valores["titulo"], valores["conteudo"], valores["tags"], valores["fixado"]
            ),
        )
        if resposta is None:
            return
        self._topico_atual = resposta.dados["identificador"]
        self.carregar_topicos()

    def responder(self):
        autor = self._exigir_usuario()
        if autor is None or self._exigir_topico() is None:
            return
        alvo = self._item_selecionado()
        if alvo is None:
            QMessageBox.information(
                self, "Sem destino", "Selecione na arvore o topico ou a mensagem a responder."
            )
            return
        dialogo = DialogoResposta(alvo["rotulo"], self)
        if dialogo.exec() != DialogoResposta.DialogCode.Accepted:
            return
        conteudo = dialogo.valores()["conteudo"]
        resposta = self._executar(
            f"Responder em {alvo['caminho']}",
            lambda: self.api.responder(alvo["identificador"], autor, conteudo),
        )
        if resposta is not None:
            self.carregar_discussao()
            self.carregar_topicos()

    def anexar(self):
        autor = self._exigir_usuario()
        if autor is None:
            return
        alvo = self._item_selecionado()
        if alvo is None or alvo["tipo"] != "mensagem":
            QMessageBox.information(
                self, "Destino invalido", "Selecione uma mensagem para receber o anexo."
            )
            return
        dialogo = DialogoAnexo(alvo["rotulo"], self)
        if dialogo.exec() != DialogoAnexo.DialogCode.Accepted:
            return
        valores = dialogo.valores()
        resposta = self._executar(
            f"Anexar em {alvo['caminho']}",
            lambda: self.api.anexar(
                alvo["identificador"], autor, valores["nome_arquivo"], valores["tamanho_kb"]
            ),
        )
        if resposta is not None:
            self.carregar_discussao()

    def votar(self):
        alvo = self._item_selecionado()
        if alvo is None or alvo["tipo"] != "mensagem":
            QMessageBox.information(
                self, "Destino invalido", "Somente mensagens recebem votos."
            )
            return
        resposta = self._executar(
            f"Votar em {alvo['caminho']}", lambda: self.api.votar(alvo["identificador"])
        )
        if resposta is not None:
            self.carregar_discussao()
            self.carregar_topicos()

    def inscrever(self):
        apelido = self._exigir_usuario()
        identificador = self._exigir_topico()
        if apelido is None or identificador is None:
            return
        resposta = self._executar(
            f"Inscrever {apelido} no topico #{identificador}",
            lambda: self.api.inscrever(identificador, apelido),
        )
        if resposta is not None:
            self.carregar_discussao()

    def alterar_estado(self):
        identificador = self._exigir_topico()
        if identificador is None:
            return
        acao = self.combo_estado.currentData()
        resposta = self._executar(
            f'Estado do topico #{identificador}: "{acao}"',
            lambda: self.api.alterar_estado(identificador, acao),
        )
        if resposta is not None:
            self.carregar_topicos()
            self.carregar_discussao()

    def buscar(self):
        termo = self.campo_busca.text().strip()
        if not termo:
            return
        resposta = self._executar(f'Buscar "{termo}"', lambda: self.api.buscar(termo))
        if resposta is None:
            return
        if not resposta.dados:
            QMessageBox.information(self, "Busca", f'Nenhum item contem "{termo}".')
            return
        linhas = [f"{item['caminho']} -> {item['rotulo']}" for item in resposta.dados]
        QMessageBox.information(
            self, "Busca", f"{len(linhas)} item(ns) encontrado(s):\n\n" + "\n".join(linhas)
        )

    def formatar_conteudo(self):
        dialogo = DialogoFormatar(self)

        def aplicar():
            valores = dialogo.valores()
            resposta = self._executar(
                "Formatar conteudo",
                lambda: self.api.formatar(
                    valores["texto"], valores["filtros"], self.usuario_atual
                ),
            )
            if resposta is not None:
                dialogo.mostrar_resultado(resposta.dados["texto"])

        dialogo.botao_aplicar.clicked.connect(aplicar)
        dialogo.exec()

    def mostrar_estatisticas(self):
        resposta = self._executar("Estatisticas", self.api.estatisticas)
        if resposta is None:
            return
        dados = resposta.dados
        texto = "\n".join(
            [
                f"Usuarios cadastrados ..: {dados['usuarios']}",
                f"Topicos abertos .......: {dados['topicos']}",
                f"Mensagens publicadas ..: {dados['mensagens']}",
                f"Itens na arvore .......: {dados['itens_na_arvore']}",
                f"Votos registrados .....: {dados['votos']}",
                f"Eventos registrados ...: {dados['eventos_registrados']}",
                f"Proximo identificador .: {dados['proximo_identificador']}",
                f"Instancia unica .......: {'sim' if dados['instancia_unica'] else 'nao'}",
            ]
        )
        QMessageBox.information(self, "Estatisticas do forum", texto)

    def mostrar_notificacoes(self):
        apelido = self._exigir_usuario()
        if apelido is None:
            return
        resposta = self._executar(
            f"Notificacoes de {apelido}", lambda: self.api.notificacoes(apelido)
        )
        if resposta is None:
            return
        if not resposta.dados:
            QMessageBox.information(self, "Notificacoes", "A caixa de entrada esta vazia.")
            return
        QMessageBox.information(self, "Notificacoes", "\n".join(resposta.dados))

    def mostrar_sobre(self):
        QMessageBox.about(
            self,
            "Sobre",
            "Forum de Discussao\n\n"
            "Projeto de Design Patterns: cliente Qt (PySide6) sobre um "
            "servidor Flask.\nO painel 'Padroes em acao' mostra, a cada "
            "requisicao, quais padroes o servidor acionou.",
        )


def perguntar_endereco(pai=None, padrao="http://127.0.0.1:5000"):
    """Dialogo simples para apontar o cliente a outro endereco do servidor."""
    endereco, confirmou = QInputDialog.getText(
        pai, "Servidor", "Endereco do servidor:", text=padrao
    )
    return endereco.strip() if confirmou and endereco.strip() else None
