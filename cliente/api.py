"""Acesso do cliente aos endpoints do servidor.

ApiForum e um proxy remoto: expoe os mesmos metodos da fachada do dominio,
mas em vez de executar a operacao, empacota a chamada em uma requisicao
HTTP. A janela grafica conversa so com esta classe e nunca monta uma URL
ou um cabecalho por conta propria.

Toda chamada devolve uma Resposta com os dados e o rastro de padroes que o
servidor acionou, que a janela exibe no painel lateral.
"""

from dataclasses import dataclass, field

import requests

ENDERECO_PADRAO = "http://127.0.0.1:5000"
TEMPO_LIMITE = 10


@dataclass
class Resposta:
    """Resultado de uma chamada bem-sucedida."""

    dados: object = None
    rastro: list = field(default_factory=list)


class ErroDaApi(Exception):
    """Erro devolvido pelo servidor ou falha de comunicacao."""

    def __init__(self, mensagem, codigo=None, rastro=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo
        self.rastro = rastro or []


class ApiForum:
    def __init__(self, endereco=ENDERECO_PADRAO, sessao=None):
        self.endereco = endereco.rstrip("/")
        self._sessao = sessao or requests.Session()

    # --- transporte ---------------------------------------------------------
    def _chamar(self, metodo, rota, **kwargs):
        url = f"{self.endereco}{rota}"
        try:
            resposta = self._sessao.request(metodo, url, timeout=TEMPO_LIMITE, **kwargs)
        except requests.RequestException as erro:
            raise ErroDaApi(
                f"Nao foi possivel falar com o servidor em {self.endereco}. "
                "Verifique se ele esta em execucao (python -m servidor)."
            ) from erro

        try:
            corpo = resposta.json()
        except ValueError as erro:
            raise ErroDaApi(
                f"O servidor respondeu algo que nao e JSON (HTTP {resposta.status_code}).",
                resposta.status_code,
            ) from erro

        if resposta.status_code >= 400:
            raise ErroDaApi(
                corpo.get("erro", "Erro desconhecido no servidor."),
                resposta.status_code,
                corpo.get("rastro"),
            )
        return Resposta(corpo.get("dados"), corpo.get("rastro") or [])

    # --- operacoes ----------------------------------------------------------
    def saude(self):
        return self._chamar("GET", "/api/saude")

    def listar_usuarios(self):
        return self._chamar("GET", "/api/usuarios")

    def cadastrar_usuario(self, apelido, email, papel="membro"):
        return self._chamar(
            "POST", "/api/usuarios",
            json={"apelido": apelido, "email": email, "papel": papel},
        )

    def notificacoes(self, apelido):
        return self._chamar("GET", f"/api/usuarios/{apelido}/notificacoes")

    def listar_topicos(self, ordenacao=None):
        parametros = {"ordenacao": ordenacao} if ordenacao else None
        return self._chamar("GET", "/api/topicos", params=parametros)

    def abrir_topico(self, autor, titulo, conteudo, tags=None, fixado=False):
        return self._chamar(
            "POST", "/api/topicos",
            json={
                "autor": autor,
                "titulo": titulo,
                "conteudo": conteudo,
                "tags": tags or [],
                "fixado": fixado,
            },
        )

    def obter_topico(self, identificador):
        return self._chamar("GET", f"/api/topicos/{identificador}")

    def inscrever(self, identificador, apelido):
        return self._chamar(
            "POST", f"/api/topicos/{identificador}/inscricoes", json={"apelido": apelido}
        )

    def alterar_estado(self, identificador, acao):
        return self._chamar(
            "PUT", f"/api/topicos/{identificador}/estado", json={"acao": acao}
        )

    def responder(self, identificador, autor, conteudo):
        return self._chamar(
            "POST", f"/api/itens/{identificador}/respostas",
            json={"autor": autor, "conteudo": conteudo},
        )

    def anexar(self, identificador, autor, nome_arquivo, tamanho_kb):
        return self._chamar(
            "POST", f"/api/mensagens/{identificador}/anexos",
            json={"autor": autor, "nome_arquivo": nome_arquivo, "tamanho_kb": tamanho_kb},
        )

    def votar(self, identificador):
        return self._chamar("POST", f"/api/mensagens/{identificador}/votos")

    def formatar(self, texto, filtros, autor=None):
        return self._chamar(
            "POST", "/api/conteudo/formatado",
            json={"texto": texto, "filtros": filtros, "autor": autor},
        )

    def buscar(self, termo):
        return self._chamar("GET", "/api/busca", params={"termo": termo})

    def estatisticas(self):
        return self._chamar("GET", "/api/estatisticas")
