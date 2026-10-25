"""Excecao de dominio compartilhada pelo servidor e pelos testes."""


class ErroDeForum(Exception):
    """Regra de negocio violada.

    O atributo `codigo` carrega o status HTTP que o servidor deve devolver,
    mas o dominio nao depende do Flask: quem traduz a excecao em resposta e
    a camada de API.
    """

    def __init__(self, mensagem, codigo=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo
