"""Padrao COMPOSITE (estrutural).

Intencao
    Compor objetos em estruturas de arvore para representar hierarquias
    todo-parte, permitindo que o cliente trate objetos individuais e
    composicoes de objetos de maneira uniforme.

Aplicacao no forum
    Uma discussao e uma arvore: o Topico contem Mensagens, cada Mensagem
    pode conter respostas (outras Mensagens) e Anexos. Exibir, contar e
    percorrer funcionam da mesma forma em qualquer nivel, porque todos os
    nos implementam a interface ItemDiscussao.

Participantes
    Componente (Component) -> ItemDiscussao
    Folha (Leaf)           -> Anexo
    Composto (Composite)   -> Mensagem, Topico
"""

from abc import ABC, abstractmethod

from ..comportamental.observer import Assunto
from ..comportamental.state import Aberto


class ItemDiscussao(ABC):
    """Componente: interface comum as folhas e aos compostos."""

    def __init__(self, identificador, autor, conteudo):
        self.identificador = identificador
        self.autor = autor
        self.conteudo = conteudo
        self.pai = None

    # --- interface uniforme -------------------------------------------------
    @property
    @abstractmethod
    def tag(self):
        """Prefixo curto usado na composicao do caminho (ex.: T1, M2, A3)."""

    @abstractmethod
    def rotulo(self):
        """Linha de texto que representa o item na arvore."""

    def filhos(self):
        """Folhas devolvem uma colecao vazia; compostos sobrescrevem."""
        return ()

    def adicionar(self, item):
        raise TypeError(f"{type(self).__name__} e uma folha e nao aceita filhos.")

    def remover(self, item):
        raise TypeError(f"{type(self).__name__} e uma folha e nao possui filhos.")

    # --- operacoes recursivas ----------------------------------------------
    def linhas(self, nivel=0):
        """Arvore achatada em linhas de texto indentadas, em pre-ordem."""
        resultado = ["   " * nivel + self.rotulo()]
        for filho in self.filhos():
            resultado.extend(filho.linhas(nivel + 1))
        return resultado

    def texto(self):
        return "\n".join(self.linhas())

    @property
    @abstractmethod
    def tipo(self):
        """Nome do tipo de no, usado na serializacao para o cliente."""

    def para_dicionario(self):
        """Serializa o no e todos os descendentes para JSON.

        A uniformidade do Composite aparece aqui: a mesma chamada funciona
        para o topico inteiro, para uma unica resposta ou para um anexo.
        """
        dados = {
            "identificador": self.identificador,
            "tipo": self.tipo,
            "tag": self.tag,
            "caminho": self.caminho(),
            "autor": self.autor.apelido,
            "conteudo": self.conteudo,
            "rotulo": self.rotulo(),
            "total_itens": self.total_itens(),
            "filhos": [filho.para_dicionario() for filho in self.filhos()],
        }
        dados.update(self._extras())
        return dados

    def _extras(self):
        """Campos adicionais de cada tipo de no."""
        return {}

    def total_itens(self):
        return 1 + sum(filho.total_itens() for filho in self.filhos())

    def total_mensagens(self):
        proprio = 1 if isinstance(self, Mensagem) else 0
        return proprio + sum(filho.total_mensagens() for filho in self.filhos())

    def total_votos(self):
        proprio = getattr(self, "votos", 0)
        return proprio + sum(filho.total_votos() for filho in self.filhos())

    def caminho(self):
        """Caminho do no a partir da raiz da discussao (ex.: /T1/M2/A3)."""
        if self.pai is None:
            return f"/{self.tag}"
        return f"{self.pai.caminho()}/{self.tag}"

    def percorrer(self):
        """Percurso em pre-ordem: o proprio no e depois os descendentes."""
        yield self
        for filho in self.filhos():
            yield from filho.percorrer()

    def raiz(self):
        return self if self.pai is None else self.pai.raiz()

    def __str__(self):
        return self.rotulo()


class Anexo(ItemDiscussao):
    """Folha: arquivo anexado a uma mensagem. Nao possui filhos."""

    def __init__(self, identificador, autor, nome_arquivo, tamanho_kb=0):
        super().__init__(identificador, autor, nome_arquivo)
        self.nome_arquivo = nome_arquivo
        self.tamanho_kb = tamanho_kb

    @property
    def tag(self):
        return f"A{self.identificador}"

    @property
    def tipo(self):
        return "anexo"

    def _extras(self):
        return {"nome_arquivo": self.nome_arquivo, "tamanho_kb": self.tamanho_kb}

    def rotulo(self):
        return f"[ANEXO #{self.identificador}] {self.nome_arquivo} ({self.tamanho_kb} KB)"


class NoComposto(ItemDiscussao):
    """Implementacao comum aos nos que armazenam filhos."""

    def __init__(self, identificador, autor, conteudo):
        super().__init__(identificador, autor, conteudo)
        self._filhos = []

    def filhos(self):
        return tuple(self._filhos)

    def adicionar(self, item):
        if not isinstance(item, ItemDiscussao):
            raise TypeError("Somente objetos ItemDiscussao podem ser adicionados.")
        item.pai = self
        self._filhos.append(item)
        return item

    def remover(self, item):
        if item not in self._filhos:
            return False
        self._filhos.remove(item)
        item.pai = None
        return True


class Mensagem(NoComposto):
    """Composto: resposta que pode conter outras respostas e anexos."""

    def __init__(self, identificador, autor, conteudo):
        super().__init__(identificador, autor, conteudo)
        self.votos = 0

    @property
    def tag(self):
        return f"M{self.identificador}"

    @property
    def tipo(self):
        return "mensagem"

    def _extras(self):
        return {"votos": self.votos}

    def votar(self):
        self.votos += 1
        return self.votos

    def rotulo(self):
        return (
            f"[MSG #{self.identificador}] {self.autor.apelido}: "
            f"{self.conteudo} (votos: {self.votos})"
        )


class Topico(NoComposto, Assunto):
    """Composto raiz da discussao.

    Acumula tres papeis de padroes diferentes:
      - Composite : e a raiz da arvore de mensagens;
      - Observer  : e o Assunto observado pelos usuarios inscritos;
      - State     : delega a um objeto EstadoTopico as regras de resposta.
    """

    def __init__(self, identificador, autor, titulo, conteudo, tags=None):
        NoComposto.__init__(self, identificador, autor, conteudo)
        Assunto.__init__(self)
        self.titulo = titulo
        self.tags = list(tags or [])
        self.fixado = False
        self._estado = Aberto()

    @property
    def tag(self):
        return f"T{self.identificador}"

    @property
    def tipo(self):
        return "topico"

    def _extras(self):
        return {
            "titulo": self.titulo,
            "tags": list(self.tags),
            "fixado": self.fixado,
            "estado": self._estado.nome,
            "aceita_resposta": self.aceita_resposta(),
            "total_respostas": self.total_respostas(),
            "total_votos": self.total_votos(),
            "inscritos": [
                observador.usuario.apelido
                for observador in self.observadores
                if hasattr(observador, "usuario")
            ],
        }

    # --- State --------------------------------------------------------------
    @property
    def estado(self):
        return self._estado

    def definir_estado(self, estado):
        self._estado = estado

    def aceita_resposta(self):
        return self._estado.pode_receber_resposta()

    def abrir(self):
        return self._estado.abrir(self)

    def fechar(self):
        return self._estado.fechar(self)

    def arquivar(self):
        return self._estado.arquivar(self)

    # --- Composite ----------------------------------------------------------
    def total_respostas(self):
        return self.total_mensagens()

    def rotulo(self):
        marcador = "[FIXADO] " if self.fixado else ""
        etiquetas = f" (tags: {', '.join(self.tags)})" if self.tags else ""
        return (
            f"[TOPICO #{self.identificador}] {marcador}{self.titulo} "
            f"<{self._estado.nome}> - por {self.autor.apelido}{etiquetas}"
        )
