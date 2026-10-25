"""Padrao OBSERVER (comportamental).

Intencao
    Definir uma dependencia um-para-muitos entre objetos, de modo que
    quando um objeto muda de estado todos os seus dependentes sao
    notificados e atualizados automaticamente.

Aplicacao no forum
    Um topico (Assunto) mantem a lista de usuarios inscritos. Quando uma
    nova resposta e publicada, todos os inscritos (Observadores) recebem
    a notificacao sem que o topico conheca a classe concreta de cada um.

Participantes
    Assunto (Subject)               -> Assunto
    Observador (Observer)           -> Observador
    Observador concreto             -> NotificadorDeUsuario, RegistroDeAtividade
"""

from abc import ABC, abstractmethod

from ..rastro import rastrear


class Observador(ABC):
    """Interface comum a todos os observadores."""

    @abstractmethod
    def atualizar(self, assunto, evento, dados):
        """Reage a um evento emitido pelo assunto observado."""


class Assunto:
    """Mantem a lista de observadores e os notifica."""

    def __init__(self):
        self._observadores = []

    @property
    def observadores(self):
        return tuple(self._observadores)

    def inscrever(self, observador):
        if observador in self._observadores:
            return False
        self._observadores.append(observador)
        return True

    def desinscrever(self, observador):
        if observador not in self._observadores:
            return False
        self._observadores.remove(observador)
        return True

    def notificar(self, evento, dados):
        total = len(self._observadores)
        rastrear("Observer", f'Notificando {total} inscrito(s) sobre o evento "{evento}"')
        if total == 0:
            rastrear(None, "  -> nenhum inscrito para notificar")
            return
        for observador in list(self._observadores):
            observador.atualizar(self, evento, dados)


class NotificadorDeUsuario(Observador):
    """Entrega a notificacao na caixa de entrada de um usuario."""

    def __init__(self, usuario):
        self.usuario = usuario

    def atualizar(self, assunto, evento, dados):
        self.usuario.caixa_entrada.append(f"[{evento}] {dados}")
        rastrear(None, f"  -> caixa de entrada de {self.usuario.apelido}: {dados}")

    def __eq__(self, outro):
        return (
            isinstance(outro, NotificadorDeUsuario)
            and outro.usuario.apelido == self.usuario.apelido
        )

    def __hash__(self):
        return hash(("NotificadorDeUsuario", self.usuario.apelido))


class RegistroDeAtividade(Observador):
    """Observador de auditoria: guarda o historico de eventos do forum."""

    def __init__(self):
        self.eventos = []

    def atualizar(self, assunto, evento, dados):
        self.eventos.append((evento, dados))
        rastrear(None, f"  -> registro de atividade: {evento} gravado (total: {len(self.eventos)})")

    def __eq__(self, outro):
        return isinstance(outro, RegistroDeAtividade)

    def __hash__(self):
        return hash("RegistroDeAtividade")
