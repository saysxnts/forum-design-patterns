"""Padrao DECORATOR (estrutural).

Intencao
    Anexar responsabilidades adicionais a um objeto dinamicamente. Os
    decoradores sao uma alternativa flexivel ao uso de heranca para
    estender funcionalidades.

Aplicacao no forum
    O texto publicado passa por filtros que podem ser combinados em
    qualquer ordem e quantidade: censura de palavras proibidas, destaque
    de moderador e assinatura do autor. Criar uma subclasse para cada
    combinacao possivel seria inviavel; os decoradores sao empilhados em
    tempo de execucao.

Participantes
    Componente (Component)   -> Conteudo
    Componente concreto      -> ConteudoSimples
    Decorador (Decorator)    -> DecoradorDeConteudo
    Decoradores concretos    -> ComCensura, ComDestaque, ComAssinatura
"""

import re
from abc import ABC, abstractmethod


class Conteudo(ABC):
    """Componente: tudo que sabe se renderizar como texto."""

    @abstractmethod
    def renderizar(self):
        """Devolve o texto final que sera exibido no forum."""

    def __str__(self):
        return self.renderizar()


class ConteudoSimples(Conteudo):
    """Componente concreto: o texto cru digitado pelo usuario."""

    def __init__(self, texto):
        self._texto = texto

    def renderizar(self):
        return self._texto


class DecoradorDeConteudo(Conteudo):
    """Decorador base: mantem a referencia ao componente envolvido."""

    def __init__(self, conteudo):
        if not isinstance(conteudo, Conteudo):
            raise TypeError("Um decorador so envolve objetos do tipo Conteudo.")
        self._conteudo = conteudo

    def renderizar(self):
        return self._conteudo.renderizar()


class ComCensura(DecoradorDeConteudo):
    """Substitui as palavras proibidas por asteriscos."""

    PALAVRAS_PROIBIDAS = ("idiota", "burro", "lixo")

    def renderizar(self):
        texto = super().renderizar()
        for palavra in self.PALAVRAS_PROIBIDAS:
            texto = re.sub(
                palavra,
                "*" * len(palavra),
                texto,
                flags=re.IGNORECASE,
            )
        return texto


class ComDestaque(DecoradorDeConteudo):
    """Marca o texto como aviso de moderacao."""

    def renderizar(self):
        return f">>> {super().renderizar()} <<<"


class ComAssinatura(DecoradorDeConteudo):
    """Acrescenta a assinatura do autor ao final do texto."""

    def __init__(self, conteudo, usuario):
        super().__init__(conteudo)
        self._usuario = usuario

    def renderizar(self):
        return f"{super().renderizar()}\n-- {self._usuario.apelido} ({self._usuario.papel})"


DECORADORES = {
    "censura": ComCensura,
    "destaque": ComDestaque,
    "assinatura": ComAssinatura,
}
