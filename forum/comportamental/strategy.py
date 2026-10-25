"""Padrao STRATEGY (comportamental).

Intencao
    Definir uma familia de algoritmos, encapsular cada um deles e
    torna-los intercambiaveis. O Strategy permite que o algoritmo varie
    independentemente dos clientes que o utilizam.

Aplicacao no forum
    A pagina inicial lista os topicos, mas a ordem depende da preferencia
    do usuario: mais recentes, mais respondidos ou mais votados. O
    contexto ListagemDeTopicos nao conhece os algoritmos; ele apenas
    delega a estrategia configurada, que pode ser trocada em execucao.

Participantes
    Contexto (Context)        -> ListagemDeTopicos
    Estrategia (Strategy)     -> EstrategiaDeOrdenacao
    Estrategias concretas     -> PorMaisRecentes, PorMaisRespondidos, PorMaisVotados
"""

from abc import ABC, abstractmethod

from ..rastro import rastrear


class EstrategiaDeOrdenacao(ABC):
    """Interface comum aos algoritmos de ordenacao."""

    nome = "indefinida"

    @abstractmethod
    def ordenar(self, topicos):
        """Devolve uma nova lista de topicos na ordem do algoritmo."""


class PorMaisRecentes(EstrategiaDeOrdenacao):
    """Identificadores maiores foram criados por ultimo."""

    nome = "mais recentes"

    def ordenar(self, topicos):
        return sorted(topicos, key=lambda t: t.identificador, reverse=True)


class PorMaisRespondidos(EstrategiaDeOrdenacao):
    nome = "mais respondidos"

    def ordenar(self, topicos):
        return sorted(topicos, key=lambda t: (-t.total_respostas(), t.identificador))


class PorMaisVotados(EstrategiaDeOrdenacao):
    nome = "mais votados"

    def ordenar(self, topicos):
        return sorted(topicos, key=lambda t: (-t.total_votos(), t.identificador))


ESTRATEGIAS = {
    "recentes": PorMaisRecentes,
    "respondidos": PorMaisRespondidos,
    "votados": PorMaisVotados,
}


class ListagemDeTopicos:
    """Contexto: usa a estrategia configurada sem conhecer o algoritmo."""

    def __init__(self, estrategia=None):
        self._estrategia = estrategia or PorMaisRecentes()

    @property
    def estrategia(self):
        return self._estrategia

    def definir_estrategia(self, estrategia):
        if type(estrategia) is type(self._estrategia):
            rastrear("Strategy", f"Estrategia mantida: {estrategia.nome}")
            return
        anterior = self._estrategia.nome
        self._estrategia = estrategia
        rastrear("Strategy", f"Estrategia trocada: {anterior} -> {estrategia.nome}")

    def listar(self, topicos):
        rastrear("Strategy", f"Ordenando os topicos por: {self._estrategia.nome}")
        return self._estrategia.ordenar(list(topicos))
