"""Padrao SINGLETON (criacional).

Intencao
    Garantir que uma classe tenha uma unica instancia e fornecer um ponto
    global de acesso a ela.

Aplicacao no forum
    Existe um unico forum em execucao. Ele concentra o cadastro de
    usuarios, a colecao de topicos e o contador de identificadores. Se
    cada parte do sistema criasse o seu proprio "Forum", os contadores e
    as colecoes ficariam dessincronizados.

Implementacao
    O controle e feito em __new__: a primeira chamada cria e guarda a
    instancia em Forum._instancia; as seguintes devolvem o mesmo objeto.
"""


class Forum:
    """Repositorio central do forum. Instancia unica."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            print("[Singleton] Primeira chamada: criando a unica instancia de Forum...")
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        self.nome = "Forum de Discussao"
        self._usuarios = {}
        self._topicos = {}
        self._proximo_identificador = 1

    # --- contador de identificadores ---------------------------------------
    def proximo_identificador(self):
        atual = self._proximo_identificador
        self._proximo_identificador += 1
        return atual

    # --- usuarios -----------------------------------------------------------
    def registrar_usuario(self, usuario):
        if usuario.apelido in self._usuarios:
            return False
        self._usuarios[usuario.apelido] = usuario
        return True

    def obter_usuario(self, apelido):
        return self._usuarios.get(apelido)

    @property
    def usuarios(self):
        return tuple(self._usuarios.values())

    # --- topicos ------------------------------------------------------------
    def adicionar_topico(self, topico):
        self._topicos[topico.identificador] = topico
        return topico

    def obter_topico(self, identificador):
        return self._topicos.get(identificador)

    @property
    def topicos(self):
        return tuple(self._topicos.values())

    # --- consultas sobre a arvore (Composite) -------------------------------
    def localizar(self, identificador):
        """Procura um item (topico, mensagem ou anexo) em todas as arvores."""
        for topico in self._topicos.values():
            for item in topico.percorrer():
                if item.identificador == identificador:
                    return item
        return None

    def buscar_por_texto(self, termo):
        """Devolve todos os itens cujo conteudo ou titulo contem o termo."""
        termo = termo.lower()
        encontrados = []
        for topico in self._topicos.values():
            for item in topico.percorrer():
                alvo = f"{getattr(item, 'titulo', '')} {item.conteudo}".lower()
                if termo in alvo:
                    encontrados.append(item)
        return encontrados

    # --- estatisticas -------------------------------------------------------
    def estatisticas(self):
        topicos = self.topicos
        return {
            "usuarios": len(self._usuarios),
            "topicos": len(topicos),
            "mensagens": sum(t.total_mensagens() for t in topicos),
            "itens_na_arvore": sum(t.total_itens() for t in topicos),
            "votos": sum(t.total_votos() for t in topicos),
            "proximo_identificador": self._proximo_identificador,
        }

    @classmethod
    def resetar(cls):
        """Descarta a instancia unica. Usado apenas pelos testes."""
        cls._instancia = None

    def __repr__(self):
        return f"<Forum id=0x{id(self):x} topicos={len(self._topicos)}>"
