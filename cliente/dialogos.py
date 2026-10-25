"""Caixas de dialogo do cliente grafico."""

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)


class _DialogoBase(QDialog):
    """Dialogo com os botoes OK/Cancelar ja ligados."""

    def __init__(self, titulo, pai=None):
        super().__init__(pai)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(420)
        self._layout = QVBoxLayout(self)

    def _adicionar_botoes(self):
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        self._layout.addWidget(botoes)
        return botoes


class DialogoUsuario(_DialogoBase):
    """Cadastro de um novo participante."""

    def __init__(self, pai=None):
        super().__init__("Cadastrar usuario", pai)
        formulario = QFormLayout()
        self.apelido = QLineEdit()
        self.email = QLineEdit()
        self.papel = QComboBox()
        self.papel.addItems(["membro", "moderador"])
        formulario.addRow("Apelido:", self.apelido)
        formulario.addRow("E-mail:", self.email)
        formulario.addRow("Papel:", self.papel)
        self._layout.addLayout(formulario)
        self._adicionar_botoes()

    def valores(self):
        return {
            "apelido": self.apelido.text().strip(),
            "email": self.email.text().strip(),
            "papel": self.papel.currentText(),
        }


class DialogoNovoTopico(_DialogoBase):
    """Reune as partes que o Builder monta no servidor."""

    def __init__(self, pai=None, pode_fixar=False):
        super().__init__("Abrir novo topico", pai)
        formulario = QFormLayout()
        self.titulo = QLineEdit()
        self.conteudo = QPlainTextEdit()
        self.conteudo.setMinimumHeight(110)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("separadas por virgula")
        self.fixado = QCheckBox("Fixar no topo da lista")
        self.fixado.setEnabled(pode_fixar)
        if not pode_fixar:
            self.fixado.setToolTip("Somente moderadores podem fixar um topico.")
        formulario.addRow("Titulo:", self.titulo)
        formulario.addRow("Texto de abertura:", self.conteudo)
        formulario.addRow("Tags:", self.tags)
        formulario.addRow("", self.fixado)
        self._layout.addLayout(formulario)
        self._adicionar_botoes()

    def valores(self):
        return {
            "titulo": self.titulo.text().strip(),
            "conteudo": self.conteudo.toPlainText().strip(),
            "tags": [t.strip() for t in self.tags.text().split(",") if t.strip()],
            "fixado": self.fixado.isChecked(),
        }


class DialogoResposta(_DialogoBase):
    def __init__(self, destino, pai=None):
        super().__init__("Responder", pai)
        self._layout.addWidget(QLabel(f"Respondendo a: {destino}"))
        self.texto = QPlainTextEdit()
        self.texto.setMinimumHeight(120)
        self._layout.addWidget(self.texto)
        self._adicionar_botoes()

    def valores(self):
        return {"conteudo": self.texto.toPlainText().strip()}


class DialogoAnexo(_DialogoBase):
    def __init__(self, destino, pai=None):
        super().__init__("Anexar arquivo", pai)
        self._layout.addWidget(QLabel(f"Anexando em: {destino}"))
        formulario = QFormLayout()
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("exemplo.py")
        self.tamanho = QSpinBox()
        self.tamanho.setRange(0, 1_000_000)
        self.tamanho.setSuffix(" KB")
        formulario.addRow("Nome do arquivo:", self.nome)
        formulario.addRow("Tamanho:", self.tamanho)
        self._layout.addLayout(formulario)
        self._adicionar_botoes()

    def valores(self):
        return {"nome_arquivo": self.nome.text().strip(), "tamanho_kb": self.tamanho.value()}


class DialogoFormatar(_DialogoBase):
    """Monta a pilha de decoradores e mostra o texto renderizado."""

    def __init__(self, pai=None):
        super().__init__("Formatar conteudo (Decorator)", pai)
        self._layout.addWidget(QLabel("Texto original:"))
        self.texto = QPlainTextEdit()
        self.texto.setMinimumHeight(90)
        self._layout.addWidget(self.texto)

        grupo = QGroupBox("Filtros, aplicados de cima para baixo")
        caixa = QVBoxLayout(grupo)
        self.censura = QCheckBox("Censura de palavras proibidas")
        self.destaque = QCheckBox("Destaque de moderacao")
        self.assinatura = QCheckBox("Assinatura do usuario atual")
        for caixinha in (self.censura, self.destaque, self.assinatura):
            caixa.addWidget(caixinha)
        self._layout.addWidget(grupo)

        self._layout.addWidget(QLabel("Resultado:"))
        self.resultado = QPlainTextEdit()
        self.resultado.setReadOnly(True)
        self.resultado.setMinimumHeight(80)
        self._layout.addWidget(self.resultado)

        botoes = self._adicionar_botoes()
        self.botao_aplicar = botoes.addButton(
            "Aplicar", QDialogButtonBox.ButtonRole.ActionRole
        )

    def filtros(self):
        escolhidos = []
        if self.censura.isChecked():
            escolhidos.append("censura")
        if self.destaque.isChecked():
            escolhidos.append("destaque")
        if self.assinatura.isChecked():
            escolhidos.append("assinatura")
        return escolhidos

    def valores(self):
        return {"texto": self.texto.toPlainText().strip(), "filtros": self.filtros()}

    def mostrar_resultado(self, texto):
        self.resultado.setPlainText(texto)
