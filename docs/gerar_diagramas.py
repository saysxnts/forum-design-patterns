"""Gera os diagramas de classes do servidor e do cliente com Graphviz.

Os diagramas sao descritos aqui em DOT e renderizados em PNG e SVG na
pasta docs/imagens/. Para regerar:

    python docs/gerar_diagramas.py

Requer o utilitario `dot` (pacote graphviz) disponivel no PATH.
"""

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IMAGENS = RAIZ / "docs" / "imagens"

CABECALHO = """
  graph [fontname="DejaVu Sans", fontsize=11, labelloc="t", rankdir=TB,
         splines=polyline, nodesep=0.35, ranksep=0.55, bgcolor="white"];
  node  [shape=record, fontname="DejaVu Sans", fontsize=9,
         style="filled", fillcolor="#f5f7fa", color="#5b6b7c"];
  edge  [fontname="DejaVu Sans", fontsize=8, color="#5b6b7c"];
"""

# seta de heranca (UML: triangulo vazio) e de uso (tracejada)
HERANCA = '[arrowhead=onormal]'
USO = '[style=dashed, arrowhead=vee]'

SERVIDOR = """
digraph servidor {
  label="Diagrama de classes - servidor (Flask + dominio)";
%(cabecalho)s
  subgraph cluster_api {
    label="Camada de API (Flask)"; style="rounded,filled"; fillcolor="#eef4ff"; color="#9db6e0";
    app [label="{servidor.app|+ criar_app(fachada) : Flask|+ responder(dados, status)\\l+ resumo_de_topico(topico)\\l+ resumo_de_item(item)\\l}"];
    rastro [label="{forum.rastro|+ iniciar()\\l+ rastrear(padrao, msg)\\l+ coletar() : list\\l}"];
  }

  subgraph cluster_facade {
    label="Facade (estrutural)"; style="rounded,filled"; fillcolor="#fff6e8"; color="#e0b96b";
    facade [label="{ForumFacade|+ cadastrar_usuario()\\l+ abrir_discussao()\\l+ responder()\\l+ anexar()\\l+ inscrever()\\l+ alterar_estado()\\l+ votar()\\l+ formatar()\\l+ buscar()\\l+ estatisticas()\\l}"];
    erro [label="{ErroDeForum|+ mensagem : str\\l+ codigo : int\\l}"];
  }

  subgraph cluster_criacional {
    label="Criacionais"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    forum [label="{Forum  «Singleton»|- _instancia : Forum\\l|+ __new__()\\l+ proximo_identificador()\\l+ registrar_usuario()\\l+ adicionar_topico()\\l+ localizar()\\l+ buscar_por_texto()\\l}"];
    criador [label="{CriadorDePublicacao  «abstrato»|+ publicar(id, autor, **dados)\\l# _fabricar()  «factory method»\\l}"];
    criador_t [label="CriadorDeTopico"];
    criador_m [label="CriadorDeMensagem"];
    criador_a [label="CriadorDeAnexo"];
    builder [label="{ConstrutorDeTopico  «Builder»|+ com_titulo()\\l+ com_autor()\\l+ com_conteudo()\\l+ com_tags()\\l+ fixado()\\l+ construir() : Topico\\l}"];
    criador_t -> criador %(heranca)s;
    criador_m -> criador %(heranca)s;
    criador_a -> criador %(heranca)s;
  }

  subgraph cluster_composite {
    label="Composite (estrutural)"; style="rounded,filled"; fillcolor="#f3eefb"; color="#ab8fd4";
    item [label="{ItemDiscussao  «abstrato»|+ identificador : int\\l+ autor : Usuario\\l+ pai : ItemDiscussao\\l|+ rotulo()\\l+ filhos()\\l+ adicionar(item)\\l+ linhas(nivel)\\l+ total_itens()\\l+ caminho()\\l+ para_dicionario()\\l}"];
    composto [label="{NoComposto|- _filhos : list\\l|+ adicionar()\\l+ remover()\\l}"];
    anexo [label="{Anexo  «folha»|+ nome_arquivo : str\\l+ tamanho_kb : int\\l}"];
    mensagem [label="{Mensagem|+ votos : int\\l|+ votar()\\l}"];
    topico [label="{Topico|+ titulo : str\\l+ tags : list\\l+ fixado : bool\\l|+ aceita_resposta()\\l+ abrir() / fechar() / arquivar()\\l}"];
    composto -> item %(heranca)s;
    anexo -> item %(heranca)s;
    mensagem -> composto %(heranca)s;
    topico -> composto %(heranca)s;
    item -> item [arrowhead=vee, headlabel="  filhos", labeldistance=2.2];
  }

  subgraph cluster_decorator {
    label="Decorator (estrutural)"; style="rounded,filled"; fillcolor="#f3eefb"; color="#ab8fd4";
    conteudo [label="{Conteudo  «abstrato»|+ renderizar() : str\\l}"];
    simples [label="ConteudoSimples"];
    decorador [label="{DecoradorDeConteudo|- _conteudo : Conteudo\\l}"];
    censura [label="ComCensura"];
    destaque [label="ComDestaque"];
    assinatura [label="ComAssinatura"];
    simples -> conteudo %(heranca)s;
    decorador -> conteudo %(heranca)s;
    censura -> decorador %(heranca)s;
    destaque -> decorador %(heranca)s;
    assinatura -> decorador %(heranca)s;
    decorador -> conteudo [arrowhead=vee, headlabel="  envolve", labeldistance=2.5];
  }

  subgraph cluster_observer {
    label="Observer (comportamental)"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    assunto [label="{Assunto|- _observadores : list\\l|+ inscrever()\\l+ desinscrever()\\l+ notificar(evento, dados)\\l}"];
    observador [label="{Observador  «abstrato»|+ atualizar(assunto, evento, dados)\\l}"];
    notificador [label="NotificadorDeUsuario"];
    registro [label="RegistroDeAtividade"];
    notificador -> observador %(heranca)s;
    registro -> observador %(heranca)s;
    assunto -> observador [arrowhead=vee, headlabel="  notifica", labeldistance=2.5];
  }

  subgraph cluster_strategy {
    label="Strategy (comportamental)"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    listagem [label="{ListagemDeTopicos  «contexto»|- _estrategia\\l|+ definir_estrategia()\\l+ listar(topicos)\\l}"];
    estrategia [label="{EstrategiaDeOrdenacao  «abstrato»|+ ordenar(topicos)\\l}"];
    recentes [label="PorMaisRecentes"];
    respondidos [label="PorMaisRespondidos"];
    votados [label="PorMaisVotados"];
    recentes -> estrategia %(heranca)s;
    respondidos -> estrategia %(heranca)s;
    votados -> estrategia %(heranca)s;
    listagem -> estrategia [arrowhead=vee, headlabel="  delega", labeldistance=2.3];
  }

  subgraph cluster_state {
    label="State (comportamental)"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    estado [label="{EstadoTopico  «abstrato»|+ pode_receber_resposta()\\l+ abrir() / fechar() / arquivar()\\l}"];
    aberto [label="Aberto"];
    fechado [label="Fechado"];
    arquivado [label="Arquivado  «terminal»"];
    aberto -> estado %(heranca)s;
    fechado -> estado %(heranca)s;
    arquivado -> estado %(heranca)s;
  }

  usuario [label="{Usuario|+ apelido : str\\l+ email : str\\l+ papel : str\\l+ caixa_entrada : list\\l}"];

  app -> facade %(uso)s;
  app -> rastro %(uso)s;
  app -> erro [style=dashed, arrowhead=vee, label="traduz em HTTP"];
  facade -> forum %(uso)s;
  facade -> builder %(uso)s;
  facade -> criador %(uso)s;
  facade -> topico %(uso)s;
  facade -> conteudo %(uso)s;
  facade -> listagem %(uso)s;
  facade -> notificador %(uso)s;
  facade -> erro %(uso)s;
  builder -> criador_t %(uso)s;
  criador -> item [style=dashed, arrowhead=vee, label="cria"];
  topico -> assunto %(heranca)s;
  topico -> estado [arrowhead=vee, headlabel="  estado atual", labeldistance=3.0];
  forum -> topico [arrowhead=vee];
  item -> usuario [arrowhead=vee, headlabel="  autor", labeldistance=2.2];
  notificador -> usuario %(uso)s;
}
"""

CLIENTE = """
digraph cliente {
  label="Diagrama de classes - cliente (PySide6)";
%(cabecalho)s
  subgraph cluster_janela {
    label="Interface grafica"; style="rounded,filled"; fillcolor="#eef4ff"; color="#9db6e0";
    janela [label="{JanelaPrincipal : QMainWindow|- api : ApiForum\\l- _topico_atual : int\\l+ combo_usuario, lista_topicos\\l+ arvore, painel_rastro\\l|+ recarregar_tudo()\\l+ carregar_usuarios()\\l+ carregar_topicos()\\l+ carregar_discussao()\\l+ abrir_topico() / responder()\\l+ anexar() / votar() / inscrever()\\l+ alterar_estado() / buscar()\\l+ formatar_conteudo()\\l# _executar(descricao, chamada)\\l# _registrar(descricao, rastro)\\l}"];
    entrada [label="{cliente.__main__|+ main(argumentos)\\l}"];
  }

  subgraph cluster_dialogos {
    label="Caixas de dialogo"; style="rounded,filled"; fillcolor="#f3eefb"; color="#ab8fd4";
    base [label="{_DialogoBase : QDialog|# _adicionar_botoes()\\l}"];
    d_usuario [label="{DialogoUsuario|+ valores()\\l}"];
    d_topico [label="{DialogoNovoTopico|+ valores()\\l}"];
    d_resposta [label="{DialogoResposta|+ valores()\\l}"];
    d_anexo [label="{DialogoAnexo|+ valores()\\l}"];
    d_formatar [label="{DialogoFormatar|+ filtros()\\l+ valores()\\l+ mostrar_resultado(texto)\\l}"];
    d_usuario -> base %(heranca)s;
    d_topico -> base %(heranca)s;
    d_resposta -> base %(heranca)s;
    d_anexo -> base %(heranca)s;
    d_formatar -> base %(heranca)s;
  }

  subgraph cluster_api {
    label="Acesso ao servidor"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    api [label="{ApiForum  «proxy remoto»|+ endereco : str\\l- _sessao : requests.Session\\l|+ cadastrar_usuario()\\l+ listar_topicos(ordenacao)\\l+ abrir_topico()\\l+ obter_topico(id)\\l+ responder() / anexar() / votar()\\l+ inscrever() / alterar_estado()\\l+ formatar() / buscar()\\l+ notificacoes() / estatisticas()\\l# _chamar(metodo, rota)\\l}"];
    resposta [label="{Resposta|+ dados : object\\l+ rastro : list\\l}"];
    erro_api [label="{ErroDaApi|+ mensagem : str\\l+ codigo : int\\l+ rastro : list\\l}"];
  }

  servidor [label="{Servidor Flask|/api/usuarios\\l/api/topicos\\l/api/itens/\\<id\\>/respostas\\l/api/mensagens/\\<id\\>/anexos\\l/api/mensagens/\\<id\\>/votos\\l/api/topicos/\\<id\\>/estado\\l/api/conteudo/formatado\\l/api/busca  /api/estatisticas\\l}",
             fillcolor="#fff6e8", color="#e0b96b"];

  entrada -> janela %(uso)s;
  entrada -> api %(uso)s;
  janela -> api [arrowhead=vee];
  janela -> base %(uso)s;
  api -> resposta [style=dashed, arrowhead=vee, label="devolve"];
  api -> erro_api [style=dashed, arrowhead=vee, label="levanta"];
  api -> servidor [label="HTTP + JSON", color="#c0392b", fontcolor="#c0392b"];
}
"""

ARQUITETURA = """
digraph arquitetura {
  label="Arquitetura da aplicacao";
  graph [fontname="DejaVu Sans", fontsize=12, labelloc="t", rankdir=LR, nodesep=0.6, ranksep=0.9];
  node  [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=10,
         fillcolor="#f5f7fa", color="#5b6b7c"];
  edge  [fontname="DejaVu Sans", fontsize=9, color="#5b6b7c"];

  subgraph cluster_c {
    label="Modulo cliente"; style="rounded,filled"; fillcolor="#eef4ff"; color="#9db6e0";
    gui [label="JanelaPrincipal\\n(PySide6)"];
    proxy [label="ApiForum\\nproxy remoto"];
    gui -> proxy;
  }

  subgraph cluster_s {
    label="Modulo servidor"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    rotas [label="Rotas Flask\\nservidor/app.py"];
    fachada [label="ForumFacade\\ncamada de servico"];
    dominio [label="Dominio\\n9 padroes GoF\\n(pacote forum)"];
    memoria [label="Forum «Singleton»\\nestado em memoria\\n(sem banco de dados)"];
    rotas -> fachada;
    fachada -> dominio;
    dominio -> memoria;
  }

  proxy -> rotas [label="HTTP / JSON", color="#c0392b", fontcolor="#c0392b"];
  rotas -> proxy [label="dados + rastro de padroes", style=dashed, color="#c0392b", fontcolor="#c0392b"];
}
"""

SERVIDOR_CRIACIONAIS = """
digraph criacionais {
  label="Diagrama de classes - servidor: padroes criacionais";
%(cabecalho)s
  subgraph cluster_servico {
    label="Camada de servico"; style="rounded,filled"; fillcolor="#fff6e8"; color="#e0b96b";
    facade [label="{ForumFacade  «Facade»|+ cadastrar_usuario()\\l+ abrir_discussao()\\l+ responder()\\l+ anexar()\\l}"];
  }

  subgraph cluster_singleton {
    label="Singleton"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    forum [label="{Forum|- _instancia : Forum  «classe»\\l- _usuarios : dict\\l- _topicos : dict\\l- _proximo_identificador : int\\l|+ __new__()  «controla a instancia»\\l+ proximo_identificador()\\l+ registrar_usuario()\\l+ obter_usuario()\\l+ adicionar_topico()\\l+ localizar(id)\\l+ buscar_por_texto(termo)\\l+ estatisticas()\\l+ resetar()  «classe, testes»\\l}"];
  }

  subgraph cluster_builder {
    label="Builder"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    builder [label="{ConstrutorDeTopico|- _titulo, _autor, _conteudo\\l- _tags, _fixado, _identificador\\l|+ com_identificador()\\l+ com_titulo()\\l+ com_autor()\\l+ com_conteudo()\\l+ com_tag() / com_tags()\\l+ fixado()\\l+ construir() : Topico\\l# _reiniciar()\\l}"];
  }

  subgraph cluster_factory {
    label="Factory Method"; style="rounded,filled"; fillcolor="#eefaf0"; color="#86c79a";
    criador [label="{CriadorDePublicacao  «abstrato»|+ tipo : str\\l|+ publicar(id, autor, **dados)\\l# _fabricar()  «factory method»\\l}"];
    criador_t [label="{CriadorDeTopico|# _fabricar() : Topico\\l}"];
    criador_m [label="{CriadorDeMensagem|# _fabricar() : Mensagem\\l}"];
    criador_a [label="{CriadorDeAnexo|# _fabricar() : Anexo\\l}"];
    criador_t -> criador %(heranca)s;
    criador_m -> criador %(heranca)s;
    criador_a -> criador %(heranca)s;
  }

  produto [label="{ItemDiscussao  «produto»|Topico | Mensagem | Anexo}", fillcolor="#f3eefb", color="#ab8fd4"];
  usuario [label="{Usuario|+ apelido, email, papel\\l+ caixa_entrada : list\\l}"];

  facade -> forum %(uso)s;
  facade -> builder %(uso)s;
  facade -> criador_m %(uso)s;
  facade -> criador_a %(uso)s;
  builder -> criador_t %(uso)s;
  criador -> produto [style=dashed, arrowhead=vee, label="cria"];
  forum -> produto [arrowhead=vee, label="guarda"];
  forum -> usuario [arrowhead=vee, label="guarda"];
}
"""

SERVIDOR_ESTRUTURAIS = """
digraph estruturais {
  label="Diagrama de classes - servidor: padroes estruturais";
%(cabecalho)s
  subgraph cluster_api {
    label="Camada de API (Flask)"; style="rounded,filled"; fillcolor="#eef4ff"; color="#9db6e0";
    app [label="{servidor.app|+ criar_app(fachada) : Flask\\l+ responder(dados, status)\\l+ resumo_de_topico()\\l+ resumo_de_item()\\l}"];
    rastro [label="{forum.rastro|+ iniciar()\\l+ rastrear(padrao, msg)\\l+ coletar() : list\\l}"];
  }

  subgraph cluster_facade {
    label="Facade"; style="rounded,filled"; fillcolor="#fff6e8"; color="#e0b96b";
    facade [label="{ForumFacade|+ abrir_discussao()\\l+ responder() / anexar()\\l+ inscrever()\\l+ alterar_estado()\\l+ votar() / formatar()\\l+ buscar() / estatisticas()\\l}"];
    erro [label="{ErroDeForum|+ mensagem : str\\l+ codigo : int\\l}"];
  }

  subgraph cluster_composite {
    label="Composite"; style="rounded,filled"; fillcolor="#f3eefb"; color="#ab8fd4";
    item [label="{ItemDiscussao  «componente»|+ identificador : int\\l+ autor : Usuario\\l+ pai : ItemDiscussao\\l|+ rotulo()  «abstrato»\\l+ tipo()  «abstrato»\\l+ filhos()\\l+ adicionar(item)\\l+ linhas(nivel)\\l+ total_itens()\\l+ total_mensagens()\\l+ caminho()\\l+ percorrer()\\l+ para_dicionario()\\l}"];
    composto [label="{NoComposto|- _filhos : list\\l|+ adicionar()\\l+ remover()\\l}"];
    anexo [label="{Anexo  «folha»|+ nome_arquivo : str\\l+ tamanho_kb : int\\l}"];
    mensagem [label="{Mensagem  «composto»|+ votos : int\\l|+ votar()\\l}"];
    topico [label="{Topico  «composto, raiz»|+ titulo : str\\l+ tags : list\\l+ fixado : bool\\l|+ aceita_resposta()\\l+ abrir() / fechar() / arquivar()\\l}"];
    composto -> item %(heranca)s;
    anexo -> item %(heranca)s;
    mensagem -> composto %(heranca)s;
    topico -> composto %(heranca)s;
    composto -> item [arrowhead=vee, label="filhos"];
  }

  subgraph cluster_decorator {
    label="Decorator"; style="rounded,filled"; fillcolor="#f3eefb"; color="#ab8fd4";
    conteudo [label="{Conteudo  «componente»|+ renderizar() : str\\l}"];
    simples [label="{ConteudoSimples|- _texto : str\\l}"];
    decorador [label="{DecoradorDeConteudo|- _conteudo : Conteudo\\l}"];
    censura [label="{ComCensura|+ PALAVRAS_PROIBIDAS\\l}"];
    destaque [label="ComDestaque"];
    assinatura [label="{ComAssinatura|- _usuario : Usuario\\l}"];
    simples -> conteudo %(heranca)s;
    decorador -> conteudo %(heranca)s;
    censura -> decorador %(heranca)s;
    destaque -> decorador %(heranca)s;
    assinatura -> decorador %(heranca)s;
    decorador -> conteudo [arrowhead=vee, label="envolve"];
  }

  app -> facade %(uso)s;
  app -> rastro %(uso)s;
  app -> erro [style=dashed, arrowhead=vee, label="traduz em HTTP"];
  facade -> topico %(uso)s;
  facade -> conteudo %(uso)s;
  facade -> erro %(uso)s;
  app -> item [style=dashed, arrowhead=vee, label="para_dicionario()"];
}
"""

SERVIDOR_COMPORTAMENTAIS = """
digraph comportamentais {
  label="Diagrama de classes - servidor: padroes comportamentais";
%(cabecalho)s
  subgraph cluster_facade {
    label="Camada de servico"; style="rounded,filled"; fillcolor="#fff6e8"; color="#e0b96b";
    facade [label="{ForumFacade|+ inscrever()\\l+ alterar_estado()\\l+ listar_topicos(ordenacao)\\l+ responder()\\l}"];
  }

  topico [label="{Topico|+ titulo : str\\l- _estado : EstadoTopico\\l|+ aceita_resposta()\\l+ abrir() / fechar() / arquivar()\\l+ definir_estado()\\l}", fillcolor="#f3eefb", color="#ab8fd4"];

  subgraph cluster_observer {
    label="Observer"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    assunto [label="{Assunto  «sujeito»|- _observadores : list\\l|+ inscrever(observador)\\l+ desinscrever(observador)\\l+ notificar(evento, dados)\\l}"];
    observador [label="{Observador  «abstrato»|+ atualizar(assunto, evento, dados)\\l}"];
    notificador [label="{NotificadorDeUsuario|+ usuario : Usuario\\l|+ atualizar()\\l+ __eq__()  «evita duplicata»\\l}"];
    registro [label="{RegistroDeAtividade|+ eventos : list\\l|+ atualizar()\\l}"];
    notificador -> observador %(heranca)s;
    registro -> observador %(heranca)s;
    assunto -> observador [arrowhead=vee, label="notifica"];
  }

  subgraph cluster_strategy {
    label="Strategy"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    listagem [label="{ListagemDeTopicos  «contexto»|- _estrategia : EstrategiaDeOrdenacao\\l|+ definir_estrategia()\\l+ listar(topicos)\\l}"];
    estrategia [label="{EstrategiaDeOrdenacao  «abstrato»|+ nome : str\\l|+ ordenar(topicos)\\l}"];
    recentes [label="{PorMaisRecentes|+ ordenar()\\l}"];
    respondidos [label="{PorMaisRespondidos|+ ordenar()\\l}"];
    votados [label="{PorMaisVotados|+ ordenar()\\l}"];
    recentes -> estrategia %(heranca)s;
    respondidos -> estrategia %(heranca)s;
    votados -> estrategia %(heranca)s;
    listagem -> estrategia [arrowhead=vee, label="delega"];
  }

  subgraph cluster_state {
    label="State"; style="rounded,filled"; fillcolor="#fdeeee"; color="#d98b8b";
    estado [label="{EstadoTopico  «abstrato»|+ nome : str\\l|+ pode_receber_resposta()\\l+ abrir(topico)\\l+ fechar(topico)\\l+ arquivar(topico)\\l# _trocar() / _recusar()\\l}"];
    aberto [label="{Aberto|pode responder: sim\\lvai para Fechado ou Arquivado\\l}"];
    fechado [label="{Fechado|pode responder: nao\\lvai para Aberto ou Arquivado\\l}"];
    arquivado [label="{Arquivado  «terminal»|pode responder: nao\\lnenhuma transicao de saida\\l}"];
    aberto -> estado %(heranca)s;
    fechado -> estado %(heranca)s;
    arquivado -> estado %(heranca)s;
  }

  facade -> listagem %(uso)s;
  facade -> notificador %(uso)s;
  facade -> topico %(uso)s;
  topico -> assunto %(heranca)s;
  topico -> estado [arrowhead=vee, label="estado atual"];
  listagem -> topico [style=dashed, arrowhead=vee, label="ordena"];
}
"""

DIAGRAMAS = {
    "servidor-classes": SERVIDOR,
    "servidor-criacionais": SERVIDOR_CRIACIONAIS,
    "servidor-estruturais": SERVIDOR_ESTRUTURAIS,
    "servidor-comportamentais": SERVIDOR_COMPORTAMENTAIS,
    "cliente-classes": CLIENTE,
    "arquitetura": ARQUITETURA,
}


def gerar():
    if not shutil.which("dot"):
        print("Aviso: o utilitario 'dot' (graphviz) nao foi encontrado. Diagramas nao gerados.")
        return False

    IMAGENS.mkdir(parents=True, exist_ok=True)
    contexto = {"cabecalho": CABECALHO, "heranca": HERANCA, "uso": USO}
    for nome, modelo in DIAGRAMAS.items():
        fonte = IMAGENS / f"{nome}.dot"
        fonte.write_text(modelo % contexto, encoding="utf-8")
        for formato in ("png", "svg"):
            subprocess.run(
                ["dot", f"-T{formato}", str(fonte), "-o", str(IMAGENS / f"{nome}.{formato}")],
                check=True,
            )
        print(f"Diagrama gerado: docs/imagens/{nome}.png")
    return True


if __name__ == "__main__":
    sys.exit(0 if gerar() else 1)
