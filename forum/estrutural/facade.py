"""Padrao FACADE (estrutural).

Intencao
    Fornecer uma interface unificada para um conjunto de interfaces de um
    subsistema. O Facade define uma interface de nivel mais alto que torna
    o subsistema mais facil de usar.

Aplicacao no forum
    Abrir uma discussao exige coordenar seis participantes: o repositorio
    unico (Singleton), o construtor passo a passo (Builder), o criador do
    produto (Factory Method), a arvore da discussao (Composite), os
    inscritos (Observer) e o estado inicial (State). O menu do programa
    nao precisa conhecer nada disso: ele chama um unico metodo do Facade.

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
from ..modelos import Usuario
from .composite import Mensagem, Topico
from .decorator import DECORADORES, ComAssinatura, ConteudoSimples


class ForumFacade:
    """Interface unica de alto nivel para todo o subsistema do forum."""

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
        if not apelido:
            print("Erro: o apelido nao pode ser vazio.")
            return None
        if self._forum.obter_usuario(apelido) is not None:
            print(f'Erro: ja existe um usuario com o apelido "{apelido}".')
            return None
        try:
            usuario = Usuario(apelido, email, papel)
        except ValueError as erro:
            print(f"Erro: {erro}")
            return None
        self._forum.registrar_usuario(usuario)
        print("[Facade] Usuario registrado no repositorio unico (Singleton).")
        print(f'Usuario "{usuario.apelido}" cadastrado como {usuario.papel}.')
        return usuario

    # --- topicos ------------------------------------------------------------
    def abrir_discussao(self, apelido_autor, titulo, conteudo, tags=None, fixado=False):
        autor = self._exigir_usuario(apelido_autor)
        if autor is None:
            return None
        if fixado and not autor.e_moderador:
            print("Erro: somente moderadores podem fixar um topico.")
            return None

        print("[Facade] Coordenando Builder + Factory Method + Singleton + Observer...")
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
            print(f"Erro: {erro}")
            return None

        self._forum.adicionar_topico(topico)
        topico.inscrever(NotificadorDeUsuario(autor))
        topico.inscrever(self._registro)
        print("[Facade] Topico armazenado no forum e observadores inscritos.")
        print(f'Topico "{topico.titulo}" aberto com sucesso em {topico.caminho()}.')
        return topico

    def responder(self, identificador_pai, apelido_autor, texto):
        autor = self._exigir_usuario(apelido_autor)
        if autor is None:
            return None
        alvo = self._forum.localizar(identificador_pai)
        if alvo is None:
            print(f"Erro: nenhum item encontrado com o identificador #{identificador_pai}.")
            return None
        if not isinstance(alvo, (Topico, Mensagem)):
            print("Erro: anexos sao folhas da arvore e nao podem receber respostas.")
            return None

        topico = alvo.raiz()
        print(f"[Facade] Verificando o estado do topico #{topico.identificador}...")
        if not topico.aceita_resposta():
            print(f"[State] O topico esta {topico.estado.nome} e nao aceita novas respostas.")
            print("Resposta nao publicada.")
            return None

        mensagem = CriadorDeMensagem().publicar(
            self._forum.proximo_identificador(), autor, conteudo=texto
        )
        alvo.adicionar(mensagem)
        print(f"[Composite] Mensagem inserida em {mensagem.caminho()}.")
        topico.notificar(
            "nova-resposta",
            f'{autor.apelido} respondeu em "{topico.titulo}"',
        )
        print("Resposta publicada com sucesso!")
        return mensagem

    def anexar(self, identificador_mensagem, apelido_autor, nome_arquivo, tamanho_kb=0):
        autor = self._exigir_usuario(apelido_autor)
        if autor is None:
            return None
        alvo = self._forum.localizar(identificador_mensagem)
        if alvo is None:
            print(f"Erro: nenhum item encontrado com o identificador #{identificador_mensagem}.")
            return None
        try:
            anexo = CriadorDeAnexo().publicar(
                self._forum.proximo_identificador(),
                autor,
                nome_arquivo=nome_arquivo,
                tamanho_kb=tamanho_kb,
            )
            alvo.adicionar(anexo)
        except TypeError as erro:
            print(f"Erro: {erro}")
            return None
        print(f"[Composite] Folha inserida em {anexo.caminho()}.")
        return anexo

    def exibir_discussao(self, identificador_topico):
        topico = self._forum.obter_topico(identificador_topico)
        if topico is None:
            print(f"Erro: topico #{identificador_topico} nao encontrado.")
            return False
        print(f"[Composite] Percorrendo a arvore a partir de {topico.caminho()}:")
        topico.exibir()
        print(f"Total de itens na arvore: {topico.total_itens()} "
              f"(respostas: {topico.total_respostas()}, votos: {topico.total_votos()}).")
        return True

    def listar_topicos(self, chave_estrategia=None):
        if chave_estrategia is not None:
            if chave_estrategia not in ESTRATEGIAS:
                print(f'Erro: estrategia desconhecida: "{chave_estrategia}".')
                return []
            self._listagem.definir_estrategia(ESTRATEGIAS[chave_estrategia]())

        topicos = self._listagem.listar(self._forum.topicos)
        if not topicos:
            print("Nenhum topico cadastrado.")
            return []
        for posicao, topico in enumerate(topicos, start=1):
            print(f"{posicao}. {topico.rotulo()}")
            print(f"   respostas: {topico.total_respostas()} | votos: {topico.total_votos()}")
        return topicos

    # --- observer -----------------------------------------------------------
    def inscrever(self, identificador_topico, apelido):
        topico = self._forum.obter_topico(identificador_topico)
        if topico is None:
            print(f"Erro: topico #{identificador_topico} nao encontrado.")
            return False
        usuario = self._exigir_usuario(apelido)
        if usuario is None:
            return False
        if not topico.inscrever(NotificadorDeUsuario(usuario)):
            print(f'Aviso: "{apelido}" ja estava inscrito neste topico.')
            return False
        print(f'[Observer] "{apelido}" inscrito. Total de observadores: '
              f"{len(topico.observadores)}.")
        return True

    def caixa_de_entrada(self, apelido):
        usuario = self._exigir_usuario(apelido)
        if usuario is None:
            return []
        if not usuario.caixa_entrada:
            print(f"A caixa de entrada de {apelido} esta vazia.")
            return []
        print(f"--- Caixa de entrada de {apelido} ---")
        for aviso in usuario.caixa_entrada:
            print(f"  {aviso}")
        return list(usuario.caixa_entrada)

    # --- state --------------------------------------------------------------
    ACOES_DE_ESTADO = ("abrir", "fechar", "arquivar")

    def alterar_estado(self, identificador_topico, acao):
        topico = self._forum.obter_topico(identificador_topico)
        if topico is None:
            print(f"Erro: topico #{identificador_topico} nao encontrado.")
            return False
        if acao not in self.ACOES_DE_ESTADO:
            print(f"Erro: acao invalida. Use uma de {self.ACOES_DE_ESTADO}.")
            return False
        print(f'[Facade] Solicitando a acao "{acao}" ao estado atual '
              f"({topico.estado.nome})...")
        mudou = getattr(topico, acao)()
        print(f"Estado atual do topico #{topico.identificador}: {topico.estado.nome}.")
        return mudou

    # --- votos --------------------------------------------------------------
    def votar(self, identificador_mensagem):
        item = self._forum.localizar(identificador_mensagem)
        if item is None:
            print(f"Erro: nenhum item encontrado com o identificador #{identificador_mensagem}.")
            return False
        if not isinstance(item, Mensagem):
            print("Erro: somente mensagens podem receber votos.")
            return False
        total = item.votar()
        print(f"Voto registrado em {item.caminho()}. Total de votos: {total}.")
        return True

    # --- decorator ----------------------------------------------------------
    def formatar(self, texto, filtros, apelido_autor=None):
        conteudo = ConteudoSimples(texto)
        aplicados = []
        for filtro in filtros:
            if filtro not in DECORADORES:
                print(f'Erro: filtro desconhecido: "{filtro}".')
                return None
            if filtro == "assinatura":
                autor = self._exigir_usuario(apelido_autor)
                if autor is None:
                    return None
                conteudo = ComAssinatura(conteudo, autor)
            else:
                conteudo = DECORADORES[filtro](conteudo)
            aplicados.append(filtro)
        print(f"[Decorator] Pilha aplicada (de dentro para fora): "
              f"{' -> '.join(aplicados) if aplicados else '(nenhum filtro)'}")
        resultado = conteudo.renderizar()
        print("--- Conteudo renderizado ---")
        print(resultado)
        return resultado

    # --- consultas ----------------------------------------------------------
    def buscar(self, termo):
        termo = (termo or "").strip()
        if not termo:
            print("Erro: o termo de busca nao pode ser vazio.")
            return []
        print(f'[Facade] Buscando "{termo}" em todas as arvores de discussao...')
        encontrados = self._forum.buscar_por_texto(termo)
        if not encontrados:
            print("Nenhum item encontrado.")
            return []
        print(f"{len(encontrados)} item(ns) encontrado(s):")
        for item in encontrados:
            print(f"  {item.caminho()} -> {item.rotulo()}")
        return encontrados

    def estatisticas(self):
        dados = self._forum.estatisticas()
        print("[Singleton] Conferindo a instancia unica: "
              f"Forum() devolve o mesmo objeto? {Forum() is self._forum}")
        print("--- Estatisticas do forum ---")
        print(f"Usuarios cadastrados ....: {dados['usuarios']}")
        print(f"Topicos abertos .........: {dados['topicos']}")
        print(f"Mensagens publicadas ....: {dados['mensagens']}")
        print(f"Itens na arvore .........: {dados['itens_na_arvore']}")
        print(f"Votos registrados .......: {dados['votos']}")
        print(f"Eventos no registro .....: {len(self._registro.eventos)}")
        print(f"Proximo identificador ...: {dados['proximo_identificador']}")
        return dados

    # --- apoio --------------------------------------------------------------
    def _exigir_usuario(self, apelido):
        usuario = self._forum.obter_usuario(apelido)
        if usuario is None:
            print(f'Erro: usuario "{apelido}" nao cadastrado.')
        return usuario
