"""Modelos de dominio que nao pertencem a nenhum padrao especifico."""


class Usuario:
    """Participante do forum.

    A caixa de entrada e preenchida pelos observadores (padrao Observer)
    sempre que um topico assinado pelo usuario recebe uma nova resposta.
    """

    PAPEIS = ("membro", "moderador")

    def __init__(self, apelido, email, papel="membro"):
        if papel not in self.PAPEIS:
            raise ValueError(f'Papel invalido: "{papel}". Use um de {self.PAPEIS}.')
        self.apelido = apelido
        self.email = email
        self.papel = papel
        self.caixa_entrada = []

    @property
    def e_moderador(self):
        return self.papel == "moderador"

    def __str__(self):
        return f"{self.apelido} ({self.papel})"

    def __repr__(self):
        return f"Usuario({self.apelido!r}, {self.email!r}, {self.papel!r})"
