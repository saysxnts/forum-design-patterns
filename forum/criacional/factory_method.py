"""Padrao FACTORY METHOD (criacional).

Intencao
    Definir uma interface para criar um objeto, mas deixar que as
    subclasses decidam qual classe instanciar. O Factory Method permite
    que uma classe delegue a instanciacao as subclasses.

Aplicacao no forum
    Publicar um item sempre segue o mesmo roteiro (anunciar, fabricar,
    confirmar). O que muda e o produto: um Topico, uma Mensagem ou um
    Anexo. O metodo publicar() e o codigo comum; _fabricar() e o Factory
    Method sobrescrito por cada criador concreto.

Participantes
    Criador (Creator)            -> CriadorDePublicacao
    Criadores concretos          -> CriadorDeTopico, CriadorDeMensagem, CriadorDeAnexo
    Produto (Product)            -> ItemDiscussao
    Produtos concretos           -> Topico, Mensagem, Anexo
"""

from abc import ABC, abstractmethod

from ..estrutural.composite import Anexo, Mensagem, Topico
from ..rastro import rastrear


class CriadorDePublicacao(ABC):
    """Criador: implementa o roteiro de publicacao e declara o Factory Method."""

    tipo = "publicacao"

    @abstractmethod
    def _fabricar(self, identificador, autor, **dados):
        """Factory Method: cada subclasse devolve o seu produto concreto."""

    def publicar(self, identificador, autor, **dados):
        rastrear("Factory Method", f"{type(self).__name__} vai fabricar um(a) {self.tipo}")
        produto = self._fabricar(identificador, autor, **dados)
        rastrear("Factory Method", f"Produto criado: {produto.rotulo()}")
        return produto


class CriadorDeTopico(CriadorDePublicacao):
    tipo = "Topico"

    def _fabricar(self, identificador, autor, **dados):
        return Topico(
            identificador,
            autor,
            dados["titulo"],
            dados.get("conteudo", ""),
            dados.get("tags"),
        )


class CriadorDeMensagem(CriadorDePublicacao):
    tipo = "Mensagem"

    def _fabricar(self, identificador, autor, **dados):
        return Mensagem(identificador, autor, dados["conteudo"])


class CriadorDeAnexo(CriadorDePublicacao):
    tipo = "Anexo"

    def _fabricar(self, identificador, autor, **dados):
        return Anexo(
            identificador,
            autor,
            dados["nome_arquivo"],
            dados.get("tamanho_kb", 0),
        )


CRIADORES = {
    "topico": CriadorDeTopico,
    "mensagem": CriadorDeMensagem,
    "anexo": CriadorDeAnexo,
}


def obter_criador(tipo):
    """Devolve uma instancia do criador registrado para o tipo informado."""
    if tipo not in CRIADORES:
        raise ValueError(f'Tipo de publicacao desconhecido: "{tipo}".')
    return CRIADORES[tipo]()
