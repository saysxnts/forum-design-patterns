"""Forum de Discussao - programa principal (menu interativo).

Trabalho de Design Patterns: nove padroes GoF aplicados a um unico
dominio. O menu abaixo e o cliente do subsistema e conversa apenas com a
fachada (ForumFacade), sem conhecer os padroes internos.

    Criacionais     Singleton, Factory Method, Builder
    Estruturais     Composite, Decorator, Facade
    Comportamentais Observer, Strategy, State

Execucao:
    python main.py
"""

from forum.estrutural.facade import ForumFacade

MENU = """
===== Forum de Discussao =====
1.  Cadastrar usuario                      [Singleton]
2.  Abrir novo topico                      [Builder + Factory Method]
3.  Responder a um topico ou mensagem      [Factory Method + State + Observer]
4.  Anexar arquivo a uma mensagem          [Composite - folha]
5.  Exibir a arvore de uma discussao       [Composite]
6.  Listar topicos                         [Strategy]
7.  Inscrever usuario em um topico         [Observer]
8.  Alterar o estado de um topico          [State]
9.  Votar em uma mensagem
10. Formatar um conteudo                   [Decorator]
11. Buscar por texto                       [Facade]
12. Ver caixa de entrada de um usuario     [Observer]
13. Estatisticas do forum                  [Singleton]
0.  Sair
Escolha uma opcao: """


def ler_texto(rotulo):
    return input(rotulo).strip()


def ler_inteiro(rotulo):
    """Le um numero inteiro; devolve None quando a entrada e invalida."""
    bruto = input(rotulo).strip()
    try:
        return int(bruto)
    except ValueError:
        print(f'Erro: "{bruto}" nao e um numero inteiro valido.')
        return None


def cadastrar_usuario(fachada):
    print("\n--- Cadastrar Usuario ---")
    apelido = ler_texto("Apelido: ")
    email = ler_texto("E-mail: ")
    papel = ler_texto("Papel (membro/moderador): ") or "membro"
    fachada.cadastrar_usuario(apelido, email, papel)


def abrir_topico(fachada):
    print("\n--- Abrir Novo Topico ---")
    autor = ler_texto("Apelido do autor: ")
    titulo = ler_texto("Titulo: ")
    conteudo = ler_texto("Texto de abertura: ")
    tags = [t.strip() for t in ler_texto("Tags (separadas por virgula): ").split(",") if t.strip()]
    fixado = ler_texto("Fixar o topico? (s/n): ").lower().startswith("s")
    fachada.abrir_discussao(autor, titulo, conteudo, tags, fixado)


def responder(fachada):
    print("\n--- Responder ---")
    identificador = ler_inteiro("Identificador do topico ou da mensagem (#): ")
    if identificador is None:
        return
    autor = ler_texto("Apelido do autor: ")
    texto = ler_texto("Resposta: ")
    fachada.responder(identificador, autor, texto)


def anexar(fachada):
    print("\n--- Anexar Arquivo ---")
    identificador = ler_inteiro("Identificador da mensagem (#): ")
    if identificador is None:
        return
    autor = ler_texto("Apelido do autor: ")
    nome = ler_texto("Nome do arquivo: ")
    tamanho = ler_inteiro("Tamanho em KB: ")
    if tamanho is None:
        return
    fachada.anexar(identificador, autor, nome, tamanho)


def exibir_discussao(fachada):
    print("\n--- Exibir Arvore da Discussao ---")
    identificador = ler_inteiro("Identificador do topico (#): ")
    if identificador is None:
        return
    fachada.exibir_discussao(identificador)


def listar_topicos(fachada):
    print("\n--- Listar Topicos ---")
    chave = ler_texto("Ordenar por (recentes/respondidos/votados): ") or "recentes"
    fachada.listar_topicos(chave)


def inscrever(fachada):
    print("\n--- Inscrever Usuario em Topico ---")
    identificador = ler_inteiro("Identificador do topico (#): ")
    if identificador is None:
        return
    apelido = ler_texto("Apelido do usuario: ")
    fachada.inscrever(identificador, apelido)


def alterar_estado(fachada):
    print("\n--- Alterar Estado do Topico ---")
    identificador = ler_inteiro("Identificador do topico (#): ")
    if identificador is None:
        return
    acao = ler_texto("Acao (abrir/fechar/arquivar): ")
    fachada.alterar_estado(identificador, acao)


def votar(fachada):
    print("\n--- Votar em Mensagem ---")
    identificador = ler_inteiro("Identificador da mensagem (#): ")
    if identificador is None:
        return
    fachada.votar(identificador)


def formatar(fachada):
    print("\n--- Formatar Conteudo ---")
    texto = ler_texto("Texto original: ")
    filtros = [
        f.strip().lower()
        for f in ler_texto("Filtros (censura/destaque/assinatura, por virgula): ").split(",")
        if f.strip()
    ]
    apelido = ler_texto("Apelido para assinatura (enter se nao usar): ") or None
    fachada.formatar(texto, filtros, apelido)


def buscar(fachada):
    print("\n--- Buscar por Texto ---")
    termo = ler_texto("Termo: ")
    fachada.buscar(termo)


def caixa_de_entrada(fachada):
    print("\n--- Caixa de Entrada ---")
    apelido = ler_texto("Apelido do usuario: ")
    fachada.caixa_de_entrada(apelido)


def estatisticas(fachada):
    print("\n--- Estatisticas ---")
    fachada.estatisticas()


OPCOES = {
    1: cadastrar_usuario,
    2: abrir_topico,
    3: responder,
    4: anexar,
    5: exibir_discussao,
    6: listar_topicos,
    7: inscrever,
    8: alterar_estado,
    9: votar,
    10: formatar,
    11: buscar,
    12: caixa_de_entrada,
    13: estatisticas,
}


def main():
    print("Inicializando o forum...")
    fachada = ForumFacade()
    print("Forum pronto. Nenhum usuario e nenhum topico cadastrados.")

    while True:
        try:
            escolha = input(MENU).strip()
        except EOFError:
            print("\nEntrada encerrada. Saindo.")
            break

        if escolha == "0":
            print("\nEncerrando o programa.")
            print("A instancia unica do Forum sera descartada pelo coletor de lixo.")
            break

        try:
            opcao = int(escolha)
        except ValueError:
            print(f'\nOpcao invalida: "{escolha}".')
            continue

        acao = OPCOES.get(opcao)
        if acao is None:
            print(f"\nOpcao invalida: {opcao}.")
            continue

        try:
            acao(fachada)
        except EOFError:
            print("\nEntrada encerrada. Saindo.")
            break


if __name__ == "__main__":
    main()
