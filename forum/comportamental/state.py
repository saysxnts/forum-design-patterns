"""Padrao STATE (comportamental).

Intencao
    Permitir que um objeto altere seu comportamento quando seu estado
    interno muda; o objeto parece mudar de classe.

Aplicacao no forum
    Um topico pode estar Aberto, Fechado ou Arquivado. A permissao para
    receber respostas e as transicoes validas ficam dentro de cada classe
    de estado, eliminando os encadeamentos de "if" espalhados pelo codigo.

Transicoes validas
    Aberto    -> Fechado, Arquivado
    Fechado   -> Aberto, Arquivado
    Arquivado -> (nenhuma: estado terminal)

Participantes
    Contexto (Context)   -> Topico (forum.estrutural.composite)
    Estado (State)       -> EstadoTopico
    Estados concretos    -> Aberto, Fechado, Arquivado
"""

from abc import ABC, abstractmethod

from ..rastro import rastrear


class EstadoTopico(ABC):
    """Interface comum aos estados de um topico."""

    nome = "indefinido"

    @abstractmethod
    def pode_receber_resposta(self):
        """Informa se o topico aceita novas respostas neste estado."""

    def abrir(self, topico):
        return self._recusar(topico, "abrir")

    def fechar(self, topico):
        return self._recusar(topico, "fechar")

    def arquivar(self, topico):
        return self._recusar(topico, "arquivar")

    def _trocar(self, topico, novo_estado):
        rastrear("State", f"Transicao: {self.nome} -> {novo_estado.nome}")
        topico.definir_estado(novo_estado)
        return True

    def _recusar(self, topico, acao):
        rastrear("State", f'Transicao recusada: nao e possivel "{acao}" um topico {self.nome}')
        return False

    def __str__(self):
        return self.nome


class Aberto(EstadoTopico):
    nome = "Aberto"

    def pode_receber_resposta(self):
        return True

    def abrir(self, topico):
        rastrear("State", "O topico ja esta Aberto")
        return False

    def fechar(self, topico):
        return self._trocar(topico, Fechado())

    def arquivar(self, topico):
        return self._trocar(topico, Arquivado())


class Fechado(EstadoTopico):
    nome = "Fechado"

    def pode_receber_resposta(self):
        return False

    def abrir(self, topico):
        return self._trocar(topico, Aberto())

    def fechar(self, topico):
        rastrear("State", "O topico ja esta Fechado")
        return False

    def arquivar(self, topico):
        return self._trocar(topico, Arquivado())


class Arquivado(EstadoTopico):
    """Estado terminal: nao permite nenhuma transicao de saida."""

    nome = "Arquivado"

    def pode_receber_resposta(self):
        return False

    def arquivar(self, topico):
        rastrear("State", "O topico ja esta Arquivado")
        return False
