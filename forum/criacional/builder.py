"""Padrao BUILDER (criacional).

Intencao
    Separar a construcao de um objeto complexo da sua representacao, de
    modo que o mesmo processo de construcao possa criar representacoes
    diferentes.

Aplicacao no forum
    Abrir um topico envolve muitas partes opcionais: titulo, autor, texto
    de abertura, lista de tags e sinalizacao de fixado. Um construtor com
    cinco parametros opcionais seria ilegivel; o Builder monta o topico
    passo a passo, valida o que e obrigatorio e so entao chama o Factory
    Method para fabricar o produto final.

Participantes
    Builder / Builder concreto -> ConstrutorDeTopico
    Produto (Product)          -> Topico
    Diretor (Director)         -> ForumFacade (forum.estrutural.facade)
"""

from .factory_method import CriadorDeTopico


class ConstrutorDeTopico:
    """Monta um Topico passo a passo. Todos os metodos sao encadeaveis."""

    def __init__(self):
        self._reiniciar()

    def _reiniciar(self):
        self._identificador = None
        self._titulo = None
        self._autor = None
        self._conteudo = ""
        self._tags = []
        self._fixado = False

    # --- passos de construcao ----------------------------------------------
    def com_identificador(self, identificador):
        self._identificador = identificador
        return self

    def com_titulo(self, titulo):
        titulo = (titulo or "").strip()
        if not titulo:
            raise ValueError("O titulo do topico nao pode ser vazio.")
        self._titulo = titulo
        return self

    def com_autor(self, autor):
        self._autor = autor
        return self

    def com_conteudo(self, conteudo):
        self._conteudo = conteudo or ""
        return self

    def com_tag(self, tag):
        tag = (tag or "").strip()
        if tag and tag not in self._tags:
            self._tags.append(tag)
        return self

    def com_tags(self, tags):
        for tag in tags or []:
            self.com_tag(tag)
        return self

    def fixado(self, valor=True):
        self._fixado = valor
        return self

    # --- entrega do produto -------------------------------------------------
    def construir(self):
        if self._identificador is None:
            raise ValueError("Builder incompleto: identificador nao informado.")
        if self._autor is None:
            raise ValueError("Builder incompleto: autor nao informado.")
        if self._titulo is None:
            raise ValueError("Builder incompleto: titulo nao informado.")

        print("[Builder] Montando o topico passo a passo:")
        print(f"  - titulo .....: {self._titulo}")
        print(f"  - autor ......: {self._autor.apelido}")
        print(f"  - conteudo ...: {self._conteudo or '(vazio)'}")
        print(f"  - tags .......: {', '.join(self._tags) if self._tags else '(nenhuma)'}")
        print(f"  - fixado .....: {'sim' if self._fixado else 'nao'}")

        topico = CriadorDeTopico().publicar(
            self._identificador,
            self._autor,
            titulo=self._titulo,
            conteudo=self._conteudo,
            tags=self._tags,
        )
        topico.fixado = self._fixado
        self._reiniciar()
        return topico
