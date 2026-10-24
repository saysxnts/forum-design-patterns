# Fórum de Discussão

Trabalho de Padrões de Projeto (Design Patterns) — implementação em Python

***

## 1. Visão geral

O projeto implementa, em Python 3 e sem nenhuma dependência externa, um fórum de discussão operado por um menu de terminal. O objetivo não é o fórum em si, e sim usar um único domínio coerente para aplicar **nove padrões de projeto do catálogo GoF** — três criacionais, três estruturais e três comportamentais — cada um resolvendo um problema real da aplicação.

Para que o papel de cada padrão fique visível durante a execução, o programa imprime uma marca entre colchetes sempre que um padrão entra em ação: `[Singleton]`, `[Builder]`, `[Factory Method]`, `[Composite]`, `[Decorator]`, `[Facade]`, `[Observer]`, `[Strategy]` e `[State]`. Essas marcas aparecem na bateria de testes da seção 4.

### 1.1 Padrões implementados

| # | Padrão | Categoria | Onde está | Papel no fórum |
|---|--------|-----------|-----------|----------------|
| 1 | Singleton | Criacional | `forum/criacional/singleton.py` | Repositório único do fórum: usuários, tópicos e contador de identificadores |
| 2 | Factory Method | Criacional | `forum/criacional/factory_method.py` | Roteiro único de publicação que fabrica Tópico, Mensagem ou Anexo |
| 3 | Builder | Criacional | `forum/criacional/builder.py` | Montagem passo a passo de um tópico (título, autor, texto, tags, fixado) |
| 4 | Composite | Estrutural | `forum/estrutural/composite.py` | Árvore da discussão: tópico → mensagens → respostas → anexos |
| 5 | Decorator | Estrutural | `forum/estrutural/decorator.py` | Filtros de conteúdo empilháveis: censura, destaque e assinatura |
| 6 | Facade | Estrutural | `forum/estrutural/facade.py` | Interface única de alto nível usada pelo menu |
| 7 | Observer | Comportamental | `forum/comportamental/observer.py` | Notificação dos usuários inscritos em um tópico |
| 8 | Strategy | Comportamental | `forum/comportamental/strategy.py` | Algoritmos de ordenação da lista de tópicos |
| 9 | State | Comportamental | `forum/comportamental/state.py` | Estados do tópico: Aberto, Fechado e Arquivado |

### 1.2 Estrutura de diretórios

```
forum-design-patterns/
├── main.py                        menu interativo (cliente do subsistema)
├── README.md
├── forum/
│   ├── __init__.py
│   ├── modelos.py                 Usuario
│   ├── criacional/
│   │   ├── singleton.py           Forum
│   │   ├── factory_method.py      CriadorDePublicacao e criadores concretos
│   │   └── builder.py             ConstrutorDeTopico
│   ├── estrutural/
│   │   ├── composite.py           ItemDiscussao, Anexo, Mensagem, Topico
│   │   ├── decorator.py           Conteudo e decoradores de texto
│   │   └── facade.py              ForumFacade
│   └── comportamental/
│       ├── observer.py            Assunto, Observador e observadores concretos
│       ├── strategy.py            EstrategiaDeOrdenacao e ListagemDeTopicos
│       └── state.py               EstadoTopico, Aberto, Fechado, Arquivado
├── testes/
│   ├── test_padroes.py            29 testes automatizados (unittest)
│   └── roteiro_bateria.txt        entradas da bateria de testes da seção 4
└── docs/
    └── DOCUMENTACAO.md            este documento
```

### 1.3 Como executar

```
python main.py                                  # menu interativo
python main.py < testes/roteiro_bateria.txt     # reproduz a bateria da seção 4
python -m unittest discover -s testes -v        # testes automatizados
```

Requisitos: Python 3.9 ou superior. Nenhuma biblioteca externa é utilizada.

***

## 2. Os nove padrões aplicados ao fórum

### 2.1 Singleton (criacional)

**Intenção.** Garantir que uma classe tenha uma única instância e fornecer um ponto global de acesso a ela.

**Problema no fórum.** O cadastro de usuários, a coleção de tópicos e o contador de identificadores precisam ser únicos. Se cada parte do sistema criasse o seu próprio objeto `Forum`, dois tópicos diferentes poderiam receber o identificador `#1` e um usuário cadastrado em um ponto não existiria no outro.

**Implementação.** O controle fica em `__new__`: a primeira chamada cria o objeto e o guarda em `Forum._instancia`; as chamadas seguintes devolvem o mesmo objeto. O método de classe `resetar()` existe apenas para isolar os testes automatizados.

### 2.2 Factory Method (criacional)

**Intenção.** Definir uma interface para criar um objeto, deixando que as subclasses decidam qual classe instanciar.

**Problema no fórum.** Publicar um item segue sempre o mesmo roteiro — anunciar, fabricar, confirmar — mas o produto varia: `Topico`, `Mensagem` ou `Anexo`.

**Implementação.** `CriadorDePublicacao.publicar()` concentra o roteiro comum e chama `_fabricar()`, o Factory Method, sobrescrito por `CriadorDeTopico`, `CriadorDeMensagem` e `CriadorDeAnexo`. O dicionário `CRIADORES` permite obter o criador pelo nome do tipo, sem `if` encadeado.

### 2.3 Builder (criacional)

**Intenção.** Separar a construção de um objeto complexo da sua representação.

**Problema no fórum.** Abrir um tópico envolve cinco informações, sendo três opcionais (texto de abertura, tags e sinalização de fixado). Um construtor com cinco parâmetros posicionais seria ilegível e frágil.

**Implementação.** `ConstrutorDeTopico` expõe métodos encadeáveis (`com_titulo`, `com_autor`, `com_tags`, `fixado`), valida o que é obrigatório em `construir()` e só então delega a fabricação ao Factory Method. Após entregar o produto, o construtor se reinicia, evitando que sobras de um tópico vazem para o próximo.

### 2.4 Composite (estrutural)

**Intenção.** Compor objetos em estruturas de árvore e tratar objetos individuais e composições de maneira uniforme.

**Problema no fórum.** Uma discussão é uma árvore: o tópico contém mensagens, cada mensagem contém respostas e anexos, sem limite de profundidade. Exibir, contar e percorrer precisam funcionar igual em qualquer nível.

**Implementação.** `ItemDiscussao` é o componente e define `exibir()`, `total_itens()`, `caminho()` e `percorrer()` de forma recursiva. `Anexo` é a folha e recusa filhos com `TypeError`; `Mensagem` e `Topico` são compostos. O método `caminho()` reconstrói o endereço do nó até a raiz (por exemplo `/T1/M3/M4/A5`), do mesmo modo que a função `mostrarCaminho` do trabalho em C.

### 2.5 Decorator (estrutural)

**Intenção.** Anexar responsabilidades a um objeto dinamicamente, como alternativa flexível à herança.

**Problema no fórum.** O texto publicado pode passar por censura de palavras proibidas, destaque de moderação e assinatura do autor, em qualquer combinação e ordem. Criar uma subclasse para cada combinação seria inviável.

**Implementação.** `Conteudo` é o componente, `ConteudoSimples` guarda o texto cru e `DecoradorDeConteudo` envolve outro `Conteudo`. Os decoradores concretos são empilhados em tempo de execução; a ordem da pilha altera o resultado final, como demonstram o Teste 12 e o teste automatizado `test_ordem_importa`.

### 2.6 Facade (estrutural)

**Intenção.** Fornecer uma interface unificada para um conjunto de interfaces de um subsistema.

**Problema no fórum.** Abrir uma discussão exige coordenar seis participantes: repositório único, construtor, criador, árvore, observadores e estado inicial. O menu não deve conhecer nada disso.

**Implementação.** `ForumFacade` oferece operações de alto nível (`abrir_discussao`, `responder`, `buscar`, `alterar_estado`) e esconde a coordenação. O arquivo `main.py` importa apenas a fachada: nenhuma classe de padrão aparece no cliente.

### 2.7 Observer (comportamental)

**Intenção.** Definir uma dependência um-para-muitos, de modo que a mudança de estado de um objeto notifique automaticamente seus dependentes.

**Problema no fórum.** Quem acompanha um tópico precisa ser avisado a cada nova resposta, e o tópico não pode depender da forma de entrega do aviso.

**Implementação.** `Topico` herda de `Assunto` e mantém a lista de observadores. `NotificadorDeUsuario` entrega o aviso na caixa de entrada de um usuário; `RegistroDeAtividade` grava o evento para auditoria. Os dois implementam a mesma interface `Observador`, e o tópico não sabe a diferença entre eles. A comparação por `__eq__` impede inscrições duplicadas do mesmo usuário.

### 2.8 Strategy (comportamental)

**Intenção.** Definir uma família de algoritmos, encapsulá-los e torná-los intercambiáveis.

**Problema no fórum.** A lista de tópicos pode ser ordenada por mais recentes, mais respondidos ou mais votados, e a escolha muda em tempo de execução.

**Implementação.** Cada algoritmo é uma classe que implementa `ordenar()`. O contexto `ListagemDeTopicos` apenas delega à estratégia configurada e pode trocá-la a qualquer momento com `definir_estrategia()`, sem nenhum `if` sobre o tipo de ordenação.

### 2.9 State (comportamental)

**Intenção.** Permitir que um objeto altere seu comportamento quando seu estado interno muda.

**Problema no fórum.** Um tópico aberto aceita respostas; fechado, não; arquivado, nunca mais volta atrás. Codificar isso com condicionais espalharia a mesma regra por vários métodos.

**Implementação.** `EstadoTopico` declara `pode_receber_resposta()` e as transições `abrir`, `fechar` e `arquivar`. Cada estado concreto autoriza apenas as transições válidas e recusa as demais; `Arquivado` é terminal. O tópico delega todas as decisões ao objeto de estado atual.

**Transições válidas.**

```
Aberto    --fechar-->    Fechado
Aberto    --arquivar-->  Arquivado
Fechado   --abrir-->     Aberto
Fechado   --arquivar-->  Arquivado
Arquivado --(nenhuma)->  estado terminal
```

***
## 3. Código-fonte completo (Python)

### Arquivo: `main.py`

{{CODIGO:main.py}}

### Arquivo: `forum/modelos.py`

{{CODIGO:forum/modelos.py}}

### Arquivo: `forum/criacional/singleton.py`

{{CODIGO:forum/criacional/singleton.py}}

### Arquivo: `forum/criacional/factory_method.py`

{{CODIGO:forum/criacional/factory_method.py}}

### Arquivo: `forum/criacional/builder.py`

{{CODIGO:forum/criacional/builder.py}}

### Arquivo: `forum/estrutural/composite.py`

{{CODIGO:forum/estrutural/composite.py}}

### Arquivo: `forum/estrutural/decorator.py`

{{CODIGO:forum/estrutural/decorator.py}}

### Arquivo: `forum/estrutural/facade.py`

{{CODIGO:forum/estrutural/facade.py}}

### Arquivo: `forum/comportamental/observer.py`

{{CODIGO:forum/comportamental/observer.py}}

### Arquivo: `forum/comportamental/strategy.py`

{{CODIGO:forum/comportamental/strategy.py}}

### Arquivo: `forum/comportamental/state.py`

{{CODIGO:forum/comportamental/state.py}}

***
## 4. Bateria de testes

### Observação sobre a estrutura de dados

O programa inicia com uma única instância de `Forum` (padrão Singleton), criada na primeira chamada a `Forum()` e reaproveitada em todas as demais. Essa instância concentra o dicionário de usuários, o dicionário de tópicos e o contador global de identificadores.

Cada tópico é a raiz de uma árvore (padrão Composite). Tópicos e mensagens guardam a lista de filhos; anexos são folhas e recusam filhos. Todo nó guarda uma referência ao pai, o que permite reconstruir o caminho até a raiz (`/T1/M3/M4/A5`) e descobrir a qual tópico uma mensagem pertence — exatamente o papel dos ponteiros `pai` e `filho` do trabalho em C.

O contador de identificadores é sequencial e **global ao fórum**, e não por tópico: o primeiro tópico recebe `#1`, o segundo `#2`, a primeira mensagem `#3`, e assim por diante. Por isso os identificadores da bateria abaixo não são contínuos dentro de uma mesma árvore.

A sequência completa de entradas desta bateria está no arquivo `testes/roteiro_bateria.txt` e pode ser reproduzida com:

```
python main.py < testes/roteiro_bateria.txt
```

### Menu principal

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
Escolha uma opcao:
```

### Teste 1 — Estado inicial: o fórum começa vazio

**Objetivo:** verificar que o fórum inicia sem nenhum tópico e que a listagem usa a estratégia padrão (mais recentes) mesmo sem dados.

**Entrada do usuário:**

```
Escolha uma opcao: 6
Ordenar por (recentes/respondidos/votados): recentes
```

**Saída esperada do programa:**

```
--- Listar Topicos ---
[Strategy] Estrategia mantida: mais recentes
[Strategy] Ordenando os topicos por: mais recentes
Nenhum topico cadastrado.
```

### Teste 2 — Cadastro de usuários no repositório único

**Objetivo:** verificar que os usuários são gravados na instância única de `Forum` e que o papel informado é respeitado.

**Entrada do usuário:**

```
Escolha uma opcao: 1
Apelido: ana
E-mail: ana@forum.com
Papel (membro/moderador): membro
Escolha uma opcao: 1
Apelido: bruno
E-mail: bruno@forum.com
Papel (membro/moderador): moderador
```

**Saída esperada do programa:**

```
--- Cadastrar Usuario ---
[Facade] Usuario registrado no repositorio unico (Singleton).
Usuario "ana" cadastrado como membro.

--- Cadastrar Usuario ---
[Facade] Usuario registrado no repositorio unico (Singleton).
Usuario "bruno" cadastrado como moderador.
```

### Teste 3 — Apelido duplicado é recusado

**Objetivo:** verificar que a instância única preserva o cadastro anterior e impede dois usuários com o mesmo apelido.

**Entrada do usuário:**

```
Escolha uma opcao: 1
Apelido: ana
E-mail: outro@forum.com
Papel (membro/moderador): membro
```

**Saída esperada do programa:**

```
--- Cadastrar Usuario ---
Erro: ja existe um usuario com o apelido "ana".
```

### Teste 4 — Abertura de tópico com Builder e Factory Method

**Objetivo:** verificar a montagem passo a passo do tópico pelo Builder, a fabricação do produto pelo Factory Method e o registro no fórum com o identificador `#1`.

**Entrada do usuário:**

```
Escolha uma opcao: 2
Apelido do autor: ana
Titulo: Como funciona a recursao em Python?
Texto de abertura: Nao entendi o caso base.
Tags (separadas por virgula): python,recursao
Fixar o topico? (s/n): n
```

**Saída esperada do programa:**

```
--- Abrir Novo Topico ---
[Facade] Coordenando Builder + Factory Method + Singleton + Observer...
[Builder] Montando o topico passo a passo:
  - titulo .....: Como funciona a recursao em Python?
  - autor ......: ana
  - conteudo ...: Nao entendi o caso base.
  - tags .......: python, recursao
  - fixado .....: nao
[Factory Method] CriadorDeTopico vai fabricar um(a) Topico...
[Factory Method] Produto criado: [TOPICO #1] Como funciona a recursao em Python? <Aberto> - por ana (tags: python, recursao)
[Facade] Topico armazenado no forum e observadores inscritos.
Topico "Como funciona a recursao em Python?" aberto com sucesso em /T1.
```

### Teste 5 — Regra de permissão e tópico fixado

**Objetivo:** verificar que a fachada valida a permissão antes de construir qualquer objeto (nenhum identificador é consumido na tentativa recusada) e que um moderador consegue fixar o tópico.

**Entrada do usuário:**

```
Escolha uma opcao: 2
Apelido do autor: ana
Titulo: Regras do forum
Texto de abertura: Leia antes de postar.
Tags (separadas por virgula): avisos
Fixar o topico? (s/n): s
Escolha uma opcao: 2
Apelido do autor: bruno
Titulo: Regras do forum
Texto de abertura: Leia antes de postar.
Tags (separadas por virgula): avisos
Fixar o topico? (s/n): s
```

**Saída esperada do programa:**

```
--- Abrir Novo Topico ---
Erro: somente moderadores podem fixar um topico.

--- Abrir Novo Topico ---
[Facade] Coordenando Builder + Factory Method + Singleton + Observer...
[Builder] Montando o topico passo a passo:
  - titulo .....: Regras do forum
  - autor ......: bruno
  - conteudo ...: Leia antes de postar.
  - tags .......: avisos
  - fixado .....: sim
[Factory Method] CriadorDeTopico vai fabricar um(a) Topico...
[Factory Method] Produto criado: [TOPICO #2] Regras do forum <Aberto> - por bruno (tags: avisos)
[Facade] Topico armazenado no forum e observadores inscritos.
Topico "Regras do forum" aberto com sucesso em /T2.
```

### Teste 6 — Inscrição de um observador no tópico

**Objetivo:** verificar que o tópico acumula observadores. O autor e o registro de atividade são inscritos automaticamente na abertura; `bruno` é o terceiro.

**Entrada do usuário:**

```
Escolha uma opcao: 7
Identificador do topico (#): 1
Apelido do usuario: bruno
```

**Saída esperada do programa:**

```
--- Inscrever Usuario em Topico ---
[Observer] "bruno" inscrito. Total de observadores: 3.
```

### Teste 7 — Resposta publicada e notificação automática

**Objetivo:** verificar a consulta ao estado antes de publicar, a fabricação da mensagem `#3`, a inserção na árvore e a notificação de todos os inscritos.

**Entrada do usuário:**

```
Escolha uma opcao: 3
Identificador do topico ou da mensagem (#): 1
Apelido do autor: bruno
Resposta: Use um caso base para parar a recursao.
```

**Saída esperada do programa:**

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

### Teste 8 — Resposta aninhada e anexo (folha da árvore)

**Objetivo:** verificar que uma mensagem pode receber respostas (nó composto) e anexos (nó folha), criando profundidade na árvore. A resposta é dirigida à mensagem `#3`, e não ao tópico.

**Entrada do usuário:**

```
Escolha uma opcao: 3
Identificador do topico ou da mensagem (#): 3
Apelido do autor: ana
Resposta: Obrigada! Funcionou aqui.
Escolha uma opcao: 4
Identificador da mensagem (#): 4
Apelido do autor: ana
Nome do arquivo: saida.txt
Tamanho em KB: 2
```

**Saída esperada do programa:**

```
--- Responder ---
[Facade] Verificando o estado do topico #1...
[Factory Method] CriadorDeMensagem vai fabricar um(a) Mensagem...
[Factory Method] Produto criado: [MSG #4] ana: Obrigada! Funcionou aqui. (votos: 0)
[Composite] Mensagem inserida em /T1/M3/M4.
[Observer] Notificando 3 inscrito(s) sobre o evento "nova-resposta"...
  -> Caixa de entrada de ana: ana respondeu em "Como funciona a recursao em Python?"
  -> Registro de atividade: evento nova-resposta gravado (total: 2).
  -> Caixa de entrada de bruno: ana respondeu em "Como funciona a recursao em Python?"
Resposta publicada com sucesso!

--- Anexar Arquivo ---
[Factory Method] CriadorDeAnexo vai fabricar um(a) Anexo...
[Factory Method] Produto criado: [ANEXO #5] saida.txt (2 KB)
[Composite] Folha inserida em /T1/M3/M4/A5.
```

### Teste 9 — Percurso recursivo da árvore da discussão

**Objetivo:** verificar que `exibir()` percorre a árvore em pré-ordem, indentando por nível, e que a contagem recursiva considera todos os nós.

**Entrada do usuário:**

```
Escolha uma opcao: 5
Identificador do topico (#): 1
```

**Saída esperada do programa:**

```
--- Exibir Arvore da Discussao ---
[Composite] Percorrendo a arvore a partir de /T1:
[TOPICO #1] Como funciona a recursao em Python? <Aberto> - por ana (tags: python, recursao)
   [MSG #3] bruno: Use um caso base para parar a recursao. (votos: 0)
      [MSG #4] ana: Obrigada! Funcionou aqui. (votos: 0)
         [ANEXO #5] saida.txt (2 KB)
Total de itens na arvore: 4 (respostas: 2, votos: 0).
```

### Teste 10 — Troca de estratégia de ordenação em tempo de execução

**Objetivo:** registrar dois votos na mensagem `#3` e verificar que a mesma lista de tópicos muda de ordem apenas por troca da estratégia, sem alterar os dados.

**Entrada do usuário:**

```
Escolha uma opcao: 9
Identificador da mensagem (#): 3
Escolha uma opcao: 9
Identificador da mensagem (#): 3
Escolha uma opcao: 6
Ordenar por (recentes/respondidos/votados): recentes
Escolha uma opcao: 6
Ordenar por (recentes/respondidos/votados): votados
```

**Saída esperada do programa:**

```
--- Votar em Mensagem ---
Voto registrado em /T1/M3. Total de votos: 1.

--- Votar em Mensagem ---
Voto registrado em /T1/M3. Total de votos: 2.

--- Listar Topicos ---
[Strategy] Estrategia mantida: mais recentes
[Strategy] Ordenando os topicos por: mais recentes
1. [TOPICO #2] [FIXADO] Regras do forum <Aberto> - por bruno (tags: avisos)
   respostas: 0 | votos: 0
2. [TOPICO #1] Como funciona a recursao em Python? <Aberto> - por ana (tags: python, recursao)
   respostas: 2 | votos: 2

--- Listar Topicos ---
[Strategy] Estrategia trocada: mais recentes -> mais votados
[Strategy] Ordenando os topicos por: mais votados
1. [TOPICO #1] Como funciona a recursao em Python? <Aberto> - por ana (tags: python, recursao)
   respostas: 2 | votos: 2
2. [TOPICO #2] [FIXADO] Regras do forum <Aberto> - por bruno (tags: avisos)
   respostas: 0 | votos: 0
```

### Teste 11 — Ciclo de vida do tópico e estado terminal

**Objetivo:** verificar as transições válidas (Aberto → Fechado → Arquivado), a recusa de resposta em tópico fechado e a impossibilidade de reabrir um tópico arquivado.

**Entrada do usuário:**

```
Escolha uma opcao: 8
Identificador do topico (#): 1
Acao (abrir/fechar/arquivar): fechar
Escolha uma opcao: 3
Identificador do topico ou da mensagem (#): 1
Apelido do autor: ana
Resposta: Posso perguntar mais uma coisa?
Escolha uma opcao: 8
Identificador do topico (#): 1
Acao (abrir/fechar/arquivar): arquivar
Escolha uma opcao: 8
Identificador do topico (#): 1
Acao (abrir/fechar/arquivar): abrir
```

**Saída esperada do programa:**

```
--- Alterar Estado do Topico ---
[Facade] Solicitando a acao "fechar" ao estado atual (Aberto)...
[State] Transicao: Aberto -> Fechado
Estado atual do topico #1: Fechado.

--- Responder ---
[Facade] Verificando o estado do topico #1...
[State] O topico esta Fechado e nao aceita novas respostas.
Resposta nao publicada.

--- Alterar Estado do Topico ---
[Facade] Solicitando a acao "arquivar" ao estado atual (Fechado)...
[State] Transicao: Fechado -> Arquivado
Estado atual do topico #1: Arquivado.

--- Alterar Estado do Topico ---
[Facade] Solicitando a acao "abrir" ao estado atual (Arquivado)...
[State] Transicao recusada: nao e possivel "abrir" um topico Arquivado.
Estado atual do topico #1: Arquivado.
```

### Teste 12 — Pilha de decoradores aplicada ao conteúdo

**Objetivo:** verificar que três filtros são empilhados sobre o mesmo texto e aplicados de dentro para fora: primeiro a censura, depois o destaque, por último a assinatura.

**Entrada do usuário:**

```
Escolha uma opcao: 10
Texto original: Esse post e um lixo, autor burro.
Filtros (censura/destaque/assinatura, por virgula): censura,destaque,assinatura
Apelido para assinatura (enter se nao usar): bruno
```

**Saída esperada do programa:**

```
--- Formatar Conteudo ---
[Decorator] Pilha aplicada (de dentro para fora): censura -> destaque -> assinatura
--- Conteudo renderizado ---
>>> Esse post e um ****, autor *****. <<<
-- bruno (moderador)
```

### Teste 13 — Busca recursiva, caixa de entrada, estatísticas e encerramento

**Objetivo:** validar a busca que percorre todas as árvores do fórum, confirmar que as notificações do Teste 7 e do Teste 8 chegaram à caixa de entrada de `ana` e conferir que `Forum()` continua devolvendo a mesma instância ao final da execução.

**Entrada do usuário:**

```
Escolha uma opcao: 11
Termo: recursao
Escolha uma opcao: 12
Apelido do usuario: ana
Escolha uma opcao: 13
Escolha uma opcao: 0
```

**Saída esperada do programa:**

```
--- Buscar por Texto ---
[Facade] Buscando "recursao" em todas as arvores de discussao...
2 item(ns) encontrado(s):
  /T1 -> [TOPICO #1] Como funciona a recursao em Python? <Arquivado> - por ana (tags: python, recursao)
  /T1/M3 -> [MSG #3] bruno: Use um caso base para parar a recursao. (votos: 2)

--- Caixa de Entrada ---
--- Caixa de entrada de ana ---
  [nova-resposta] bruno respondeu em "Como funciona a recursao em Python?"
  [nova-resposta] ana respondeu em "Como funciona a recursao em Python?"

--- Estatisticas ---
[Singleton] Conferindo a instancia unica: Forum() devolve o mesmo objeto? True
--- Estatisticas do forum ---
Usuarios cadastrados ....: 2
Topicos abertos .........: 2
Mensagens publicadas ....: 2
Itens na arvore .........: 5
Votos registrados .......: 2
Eventos no registro .....: 2
Proximo identificador ...: 6

Encerrando o programa.
A instancia unica do Forum sera descartada pelo coletor de lixo.
```

***

## 5. Testes automatizados

Além da bateria interativa, o projeto traz 29 testes automatizados em `testes/test_padroes.py`, agrupados por padrão. Cada teste roda com um fórum limpo (`Forum.resetar()`) e com a saída do programa redirecionada, de modo que a verificação é feita sobre o estado dos objetos, e não sobre o texto impresso.

**Comando:**

```
python -m unittest discover -s testes -v
```

**Resultado:**

```
test_builder_incompleto (test_padroes.TesteBuilder.test_builder_incompleto) ... ok
test_construcao_encadeada (test_padroes.TesteBuilder.test_construcao_encadeada) ... ok
test_reinicia_apos_construir (test_padroes.TesteBuilder.test_reinicia_apos_construir) ... ok
test_caminho_ate_a_raiz (test_padroes.TesteComposite.test_caminho_ate_a_raiz) ... ok
test_contagem_recursiva (test_padroes.TesteComposite.test_contagem_recursiva) ... ok
test_folha_nao_aceita_filhos (test_padroes.TesteComposite.test_folha_nao_aceita_filhos) ... ok
test_censura (test_padroes.TesteDecorator.test_censura) ... ok
test_ordem_importa (test_padroes.TesteDecorator.test_ordem_importa) ... ok
test_pilha_de_decoradores (test_padroes.TesteDecorator.test_pilha_de_decoradores) ... ok
test_busca_recursiva (test_padroes.TesteFacade.test_busca_recursiva) ... ok
test_fluxo_completo (test_padroes.TesteFacade.test_fluxo_completo) ... ok
test_somente_moderador_fixa (test_padroes.TesteFacade.test_somente_moderador_fixa) ... ok
test_topico_fechado_recusa_resposta (test_padroes.TesteFacade.test_topico_fechado_recusa_resposta) ... ok
test_usuario_duplicado (test_padroes.TesteFacade.test_usuario_duplicado) ... ok
test_cada_criador_devolve_seu_produto (test_padroes.TesteFactoryMethod.test_cada_criador_devolve_seu_produto) ... ok
test_criador_por_nome (test_padroes.TesteFactoryMethod.test_criador_por_nome) ... ok
test_tipo_desconhecido (test_padroes.TesteFactoryMethod.test_tipo_desconhecido) ... ok
test_desinscrever (test_padroes.TesteObserver.test_desinscrever) ... ok
test_nao_duplica_inscricao (test_padroes.TesteObserver.test_nao_duplica_inscricao) ... ok
test_notifica_inscritos (test_padroes.TesteObserver.test_notifica_inscritos) ... ok
test_contador_nao_reinicia (test_padroes.TesteSingleton.test_contador_nao_reinicia) ... ok
test_estado_compartilhado (test_padroes.TesteSingleton.test_estado_compartilhado) ... ok
test_instancia_unica (test_padroes.TesteSingleton.test_instancia_unica) ... ok
test_arquivado_e_terminal (test_padroes.TesteState.test_arquivado_e_terminal) ... ok
test_estado_inicial (test_padroes.TesteState.test_estado_inicial) ... ok
test_fechar_bloqueia_respostas (test_padroes.TesteState.test_fechar_bloqueia_respostas) ... ok
test_mais_recentes (test_padroes.TesteStrategy.test_mais_recentes) ... ok
test_mais_respondidos (test_padroes.TesteStrategy.test_mais_respondidos) ... ok
test_troca_em_execucao (test_padroes.TesteStrategy.test_troca_em_execucao) ... ok

----------------------------------------------------------------------
Ran 29 tests in 0.004s

OK
```
