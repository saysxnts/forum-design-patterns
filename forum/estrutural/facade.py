"""Padrao FACADE (estrutural).

Intencao
    Fornecer uma interface unificada para um conjunto de interfaces de um
    subsistema. O Facade define uma interface de nivel mais alto que torna
    o subsistema mais facil de usar.

Aplicacao no forum
    Abrir uma discussao exige coordenar seis participantes: o repositorio
    unico (Singleton), o construtor passo a passo (Builder), o criador do
    produto (Factory Method), a arvore da discussao (Composite), os
    inscritos (Observer) e o estado inicial (State). Quem chama precisa de
    um unico metodo.

    No projeto cliente/servidor esta fachada e a camada de servico do
    servidor Flask: cada endpoint chama um metodo daqui e traduz o
    resultado em JSON. Nenhuma rota conhece as classes dos padroes, e o
    dominio nao importa nada do Flask.

Erros
    A fachada nao imprime mensagens: em caso de regra violada ela levanta
    ErroDeForum com o status HTTP adequado, e a camada de API traduz a
    excecao em resposta.

Participantes
    Facade     -> ForumFacade
    Subsistema -> Forum, ConstrutorDeTopico, criadores, Topico/Mensagem/Anexo,
                  observadores, estados e estrategias de ordenacao
"""

from ..comportamental.observer import NotificadorDeUsuario, RegistroDeAtividade
from ..comportamental.strategy import ESTRATEGIAS, ListagemDeTopicos, PorMaisRecentes
from ..criacional.builder import ConstrutorDeTopico
from ..criacional.factory_method import CriadorDeAnexo, CriadorDeMensagem
from ..criacional.singleton import Forum
from ..erros import ErroDeForum
from ..modelos import Usuario
from ..rastro import rastrear
from .composite import Mensagem, Topico
from .decorator import DECORADORES, ComAssinatura, ConteudoSimples


class ForumFacade:
    """Interface unica de alto nivel para todo o subsistema do forum."""

    ACOES_DE_ESTADO = ("abrir", "fechar", "arquivar")

    def __init__(self):
        self._forum = Forum()
        self._construtor = ConstrutorDeTopico()
        self._listagem = ListagemDeTopicos(PorMaisRecentes())
        self._registro = RegistroDeAtividade()

    @property
    def forum(self):
        return self._forum

    @property
    def registro(self):
        return self._registro

    # --- usuarios -----------------------------------------------------------
    def cadastrar_usuario(self, apelido, email, papel="membro"):
        apelido = (apelido or "").strip()
        email = (email or "").strip()
        if not apelido:
            raise ErroDeForum("O apelido nao pode ser vazio.", 400)
        if not email:
            raise ErroDeForum("O e-mail nao pode ser vazio.", 400)
        if self._forum.obter_usuario(apelido) is not None:
            raise ErroDeForum(f'Ja existe um usuario com o apelido "{apelido}".', 409)
        try:
            usuario = Usuario(apelido, email, papel)
        except ValueError as erro:
            raise ErroDeForum(str(erro), 400) from erro

        self._forum.registrar_usuario(usuario)
        rastrear("Facade", f'Usuario "{usuario.apelido}" gravado no repositorio unico')
        return usuario

    def listar_usuarios(self):
        return list(self._forum.usuarios)

    def obter_usuario(self, apelido):
        usuario = self._forum.obter_usuario((apelido or "").strip())
        if usuario is None:
            raise ErroDeForum(f'Usuario "{apelido}" nao cadastrado.', 404)
        return usuario

    def caixa_de_entrada(self, apelido):
        return list(self.obter_usuario(apelido).caixa_entrada)

    # --- topicos ------------------------------------------------------------
    def abrir_discussao(self, apelido_autor, titulo, conteudo="", tags=None, fixado=False):
        autor = self.obter_usuario(apelido_autor)
        if fixado and not autor.e_moderador:
            raise ErroDeForum("Somente moderadores podem fixar um topico.", 403)

        rastrear("Facade", "Coordenando Builder + Factory Method + Singleton + Observer")
        try:
            topico = (
                self._construtor.com_identificador(self._forum.proximo_identificador())
                .com_titulo(titulo)
                .com_autor(autor)
                .com_conteudo(conteudo)
                .com_tags(tags)
                .fixado(fixado)
                .construir()
            )
        except ValueError as erro:
            raise ErroDeForum(str(erro), 400) from erro

        self._forum.adicionar_topico(topico)
        topico.inscrever(NotificadorDeUsuario(autor))
        topico.inscrever(self._registro)
        rastrear("Facade", f"Topico guardado em {topico.caminho()} e observadores inscritos")
        return topico

    def obter_topico(self, identificador):
        topico = self._forum.obter_topico(identificador)
        if topico is None:
            raise ErroDeForum(f"Topico #{identificador} nao encontrado.", 404)
        rastrear("Composite", f"Percorrendo a arvore a partir de {topico.caminho()}")
        return topico

    def listar_topicos(self, chave_estrategia=None):
        if chave_estrategia:
            if chave_estrategia not in ESTRATEGIAS:
                validas = ", ".join(ESTRATEGIAS)
                raise ErroDeForum(
                    f'Ordenacao desconhecida: "{chave_estrategia}". Use uma de: {validas}.', 400
                )
            self._listagem.definir_estrategia(ESTRATEGIAS[chave_estrategia]())
        return self._listagem.listar(self._forum.topicos)

    def responder(self, identificador_pai, apelido_autor, texto):
        autor = self.obter_usuario(apelido_autor)
        texto = (texto or "").strip()
        if not texto:
            raise ErroDeForum("A resposta nao pode ser vazia.", 400)

        alvo = self._localizar(identificador_pai)
        if not isinstance(alvo, (Topico, Mensagem)):
            raise ErroDeForum("Anexos sao folhas da arvore e nao recebem respostas.", 400)

        topico = alvo.raiz()
        rastrear("Facade", f"Consultando o estado do topico #{topico.identificador}")
        if not topico.aceita_resposta():
            raise ErroDeForum(
                f"O topico esta {topico.estado.nome} e nao aceita novas respostas.", 409
            )

        mensagem = CriadorDeMensagem().publicar(
            self._forum.proximo_identificador(), autor, conteudo=texto
        )
        alvo.adicionar(mensagem)
        rastrear("Composite", f"Mensagem inserida em {mensagem.caminho()}")
        topico.notificar("nova-resposta", f'{autor.apelido} respondeu em "{topico.titulo}"')
        return mensagem

    def anexar(self, identificador_mensagem, apelido_autor, nome_arquivo, tamanho_kb=0):
        autor = self.obter_usuario(apelido_autor)
        nome_arquivo = (nome_arquivo or "").strip()
        if not nome_arquivo:
            raise ErroDeForum("O nome do arquivo nao pode ser vazio.", 400)
        try:
            tamanho_kb = int(tamanho_kb)
        except (TypeError, ValueError) as erro:
            raise ErroDeForum("O tamanho do anexo deve ser um numero inteiro.", 400) from erro
        if tamanho_kb < 0:
            raise ErroDeForum("O tamanho do anexo nao pode ser negativo.", 400)

        alvo = self._localizar(identificador_mensagem)
        try:
            anexo = CriadorDeAnexo().publicar(
                self._forum.proximo_identificador(),
                autor,
                nome_arquivo=nome_arquivo,
                tamanho_kb=tamanho_kb,
            )
            alvo.adicionar(anexo)
        except TypeError as erro:
            raise ErroDeForum(str(erro), 400) from erro
        rastrear("Composite", f"Folha inserida em {anexo.caminho()}")
        return anexo

    # --- observer -----------------------------------------------------------
    def inscrever(self, identificador_topico, apelido):
        topico = self._forum.obter_topico(identificador_topico)
        if topico is None:
            raise ErroDeForum(f"Topico #{identificador_topico} nao encontrado.", 404)
        usuario = self.obter_usuario(apelido)
        if not topico.inscrever(NotificadorDeUsuario(usuario)):
            raise ErroDeForum(f'"{apelido}" ja esta inscrito neste topico.', 409)
        rastrear(
            "Observer",
            f'"{apelido}" inscrito. Total de observadores: {len(topico.observadores)}',
        )
        return topico

    # --- state --------------------------------------------------------------
    def alterar_estado(self, identificador_topico, acao):
        topico = self._forum.obter_topico(identificador_topico)
        if topico is None:
            raise ErroDeForum(f"Topico #{identificador_topico} nao encontrado.", 404)
        if acao not in self.ACOES_DE_ESTADO:
            validas = ", ".join(self.ACOES_DE_ESTADO)
            raise ErroDeForum(f'Acao invalida: "{acao}". Use uma de: {validas}.', 400)

        anterior = topico.estado.nome
        rastrear("Facade", f'Pedindo "{acao}" ao estado atual ({anterior})')
        if not getattr(topico, acao)():
            raise ErroDeForum(
                f'Nao e possivel "{acao}" um topico {anterior}.', 409
            )
        return topico

    # --- votos --------------------------------------------------------------
    def votar(self, identificador_mensagem):
        item = self._localizar(identificador_mensagem)
        if not isinstance(item, Mensagem):
            raise ErroDeForum("Somente mensagens podem receber votos.", 400)
        total = item.votar()
        rastrear(None, f"Voto registrado em {item.caminho()} (total: {total})")
        return item

    # --- decorator ----------------------------------------------------------
    def formatar(self, texto, filtros, apelido_autor=None):
        if texto is None or not str(texto).strip():
            raise ErroDeForum("O texto a formatar nao pode ser vazio.", 400)

        conteudo = ConteudoSimples(texto)
        aplicados = []
        for filtro in filtros or []:
            if filtro not in DECORADORES:
                validos = ", ".join(DECORADORES)
                raise ErroDeForum(
                    f'Filtro desconhecido: "{filtro}". Use um de: {validos}.', 400
                )
            if filtro == "assinatura":
                conteudo = ComAssinatura(conteudo, self.obter_usuario(apelido_autor))
            else:
                conteudo = DECORADORES[filtro](conteudo)
            aplicados.append(filtro)

        rastrear(
            "Decorator",
            "Pilha aplicada (de dentro para fora): "
            + (" -> ".join(aplicados) if aplicados else "(nenhum filtro)"),
        )
        return conteudo.renderizar()

    # --- consultas ----------------------------------------------------------
    def buscar(self, termo):
        termo = (termo or "").strip()
        if not termo:
            raise ErroDeForum("O termo de busca nao pode ser vazio.", 400)
        rastrear("Facade", f'Buscando "{termo}" em todas as arvores de discussao')
        encontrados = self._forum.buscar_por_texto(termo)
        rastrear(None, f"{len(encontrados)} item(ns) encontrado(s)")
        return encontrados

    def estatisticas(self):
        dados = self._forum.estatisticas()
        dados["eventos_registrados"] = len(self._registro.eventos)
        dados["instancia_unica"] = Forum() is self._forum
        rastrear(
            "Singleton",
            f"Forum() devolve o mesmo objeto? {dados['instancia_unica']}",
        )
        return dados

    # --- apoio --------------------------------------------------------------
    def _localizar(self, identificador):
        item = self._forum.localizar(identificador)
        if item is None:
            raise ErroDeForum(f"Nenhum item encontrado com o identificador #{identificador}.", 404)
        return item
