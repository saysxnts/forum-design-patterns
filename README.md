# Fórum de Discussão — Design Patterns em Python

Projeto acadêmico que aplica **nove padrões de projeto do catálogo GoF** a um único domínio coerente: um fórum de discussão operado por menu de terminal. Python 3, sem dependências externas.

A ideia não é o fórum em si, e sim mostrar cada padrão resolvendo um problema real da aplicação — e deixar isso visível em tempo de execução: o programa imprime uma marca como `[Observer]` ou `[State]` sempre que um padrão entra em ação.

## Padrões implementados

| Padrão | Categoria | Arquivo | Papel no fórum |
|---|---|---|---|
| Singleton | Criacional | `forum/criacional/singleton.py` | Repositório único: usuários, tópicos e contador de identificadores |
| Factory Method | Criacional | `forum/criacional/factory_method.py` | Roteiro único de publicação que fabrica Tópico, Mensagem ou Anexo |
| Builder | Criacional | `forum/criacional/builder.py` | Montagem passo a passo de um tópico (título, autor, texto, tags, fixado) |
| Composite | Estrutural | `forum/estrutural/composite.py` | Árvore da discussão: tópico → mensagens → respostas → anexos |
| Decorator | Estrutural | `forum/estrutural/decorator.py` | Filtros de conteúdo empilháveis: censura, destaque e assinatura |
| Facade | Estrutural | `forum/estrutural/facade.py` | Interface única de alto nível usada pelo menu |
| Observer | Comportamental | `forum/comportamental/observer.py` | Notificação dos inscritos a cada nova resposta |
| Strategy | Comportamental | `forum/comportamental/strategy.py` | Ordenação da lista de tópicos (recentes, respondidos, votados) |
| State | Comportamental | `forum/comportamental/state.py` | Ciclo de vida do tópico: Aberto, Fechado e Arquivado |

## Como executar

Requisito: Python 3.9 ou superior.

```bash
python main.py                                  # menu interativo
python main.py < testes/roteiro_bateria.txt     # reproduz a bateria de testes da documentação
python -m unittest discover -s testes -v        # 29 testes automatizados
```

## Menu

```
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
```

## Exemplo de execução

Publicar uma resposta aciona quatro padrões em sequência — a fachada consulta o estado, o criador fabrica o produto, a árvore recebe o nó e os inscritos são notificados:

```
--- Responder ---
[Facade] Verificando o estado do topico #1...
[Factory Method] CriadorDeMensagem vai fabricar um(a) Mensagem...
[Factory Method] Produto criado: [MSG #3] bruno: Use um caso base para parar a recursao. (votos: 0)
[Composite] Mensagem inserida em /T1/M3.
[Observer] Notificando 3 inscrito(s) sobre o evento "nova-resposta"...
  -> Caixa de entrada de ana: bruno respondeu em "Como funciona a recursao em Python?"
  -> Registro de atividade: evento nova-resposta gravado (total: 1).
  -> Caixa de entrada de bruno: bruno respondeu em "Como funciona a recursao em Python?"
Resposta publicada com sucesso!
```

E a árvore da discussão (Composite) exibida em qualquer profundidade:

```
[TOPICO #1] Como funciona a recursao em Python? <Aberto> - por ana (tags: python, recursao)
   [MSG #3] bruno: Use um caso base para parar a recursao. (votos: 0)
      [MSG #4] ana: Obrigada! Funcionou aqui. (votos: 0)
         [ANEXO #5] saida.txt (2 KB)
```

## Estrutura do projeto

```
forum-design-patterns/
├── main.py                        menu interativo (cliente do subsistema)
├── forum/
│   ├── modelos.py                 Usuario
│   ├── criacional/                singleton.py, factory_method.py, builder.py
│   ├── estrutural/                composite.py, decorator.py, facade.py
│   └── comportamental/            observer.py, strategy.py, state.py
├── testes/
│   ├── test_padroes.py            29 testes automatizados (unittest)
│   └── roteiro_bateria.txt        entradas da bateria de testes documentada
└── docs/
    ├── DOCUMENTACAO.md            documentação completa
    ├── Forum_Discussao_Design_Patterns.pdf
    └── gerar_documentacao.py      regera o Markdown e o PDF
```

## Documentação

A documentação completa está em [`docs/DOCUMENTACAO.md`](docs/DOCUMENTACAO.md) e no PDF em [`docs/Forum_Discussao_Design_Patterns.pdf`](docs/Forum_Discussao_Design_Patterns.pdf). Ela traz a intenção de cada padrão, o problema concreto que ele resolve no fórum, o código-fonte completo e uma bateria de 13 testes com objetivo, entrada e saída esperada.

Para regerar os dois arquivos após alterar o código:

```bash
python docs/gerar_documentacao.py
```

O script reinsere o código-fonte real dentro do texto, então a documentação nunca fica fora de sincronia com os arquivos `.py`.

## Decisões de projeto

- **Sem dependências externas.** Só a biblioteca padrão, para rodar em qualquer máquina com Python 3.9+.
- **Um padrão por arquivo**, agrupado por categoria GoF, com o cabeçalho do módulo documentando intenção, aplicação e participantes.
- **O cliente não conhece os padrões.** `main.py` importa apenas `ForumFacade`; nenhuma classe de padrão aparece no menu.
- **Marcas de execução.** As linhas `[Padrão]` existem para fins didáticos: tornam visível qual padrão está agindo a cada operação.
