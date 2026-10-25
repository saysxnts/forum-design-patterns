# Fórum de Discussão — Design Patterns em Python

Projeto de **Paradigmas de Programação (CC5AN)**: aplicação cliente/servidor com **nove padrões de projeto do catálogo GoF** aplicados ao domínio de um fórum de discussão.

- **Servidor** — Flask, com um endpoint para cada recurso.
- **Cliente** — interface gráfica em Qt (PySide6) que consome esses endpoints.
- Sem banco de dados, API de terceiros, serviço de nuvem ou serviço de IA.

Para tornar os padrões visíveis durante a demonstração, **toda resposta do servidor traz o rastro dos padrões acionados naquela requisição**, e o cliente mostra esse rastro em um painel lateral.

![Janela principal do cliente](docs/imagens/cliente-janela-principal.png)

## Como executar

```bash
pip install -r requirements.txt

python -m servidor     # terminal 1 — http://127.0.0.1:5000
python -m cliente      # terminal 2 — interface gráfica
```

O cliente aceita outro endereço: `python -m cliente http://127.0.0.1:5050`.

Requisito: Python 3.9 ou superior.

## Padrões implementados

| Padrão | Categoria | Arquivo | Papel no fórum |
|---|---|---|---|
| Singleton | Criacional | `forum/criacional/singleton.py` | Repositório único: usuários, tópicos e contador de identificadores |
| Factory Method | Criacional | `forum/criacional/factory_method.py` | Roteiro único de publicação que fabrica Tópico, Mensagem ou Anexo |
| Builder | Criacional | `forum/criacional/builder.py` | Montagem passo a passo de um tópico |
| Composite | Estrutural | `forum/estrutural/composite.py` | Árvore da discussão e sua serialização para JSON |
| Decorator | Estrutural | `forum/estrutural/decorator.py` | Filtros de conteúdo empilháveis |
| Facade | Estrutural | `forum/estrutural/facade.py` | Camada de serviço chamada pelas rotas Flask |
| Observer | Comportamental | `forum/comportamental/observer.py` | Notificação dos inscritos a cada nova resposta |
| Strategy | Comportamental | `forum/comportamental/strategy.py` | Ordenação da listagem de tópicos |
| State | Comportamental | `forum/comportamental/state.py` | Ciclo de vida do tópico: Aberto, Fechado e Arquivado |

No cliente, `ApiForum` funciona como **proxy remoto**: expõe os mesmos métodos da fachada do servidor, mas empacota cada chamada em uma requisição HTTP.

## Endpoints

| Método | Rota | Padrões acionados |
|---|---|---|
| `GET` | `/api/usuarios` | — |
| `POST` | `/api/usuarios` | Facade, Singleton |
| `GET` | `/api/usuarios/<apelido>/notificacoes` | Observer |
| `GET` | `/api/topicos?ordenacao=` | Strategy |
| `POST` | `/api/topicos` | Builder, Factory Method, Observer |
| `GET` | `/api/topicos/<id>` | Composite |
| `POST` | `/api/topicos/<id>/inscricoes` | Observer |
| `PUT` | `/api/topicos/<id>/estado` | State |
| `POST` | `/api/itens/<id>/respostas` | State, Factory Method, Composite, Observer |
| `POST` | `/api/mensagens/<id>/anexos` | Factory Method, Composite |
| `POST` | `/api/mensagens/<id>/votos` | Composite |
| `POST` | `/api/conteudo/formatado` | Decorator |
| `GET` | `/api/busca?termo=` | Facade, Composite |
| `GET` | `/api/estatisticas` | Singleton |

Toda resposta segue o mesmo envelope:

```json
{
  "dados": { "...": "resultado da operação" },
  "rastro": [
    "[Facade] Coordenando Builder + Factory Method + Singleton + Observer",
    "[Builder] Montando o topico passo a passo:",
    "[Factory Method] CriadorDeTopico vai fabricar um(a) Topico"
  ]
}
```

Em caso de erro, `{"erro": "...", "rastro": [...]}` com o status HTTP adequado (400, 403, 404, 405 ou 409).

## Testes

```bash
python -m unittest discover -s testes -v     # 90 testes
python testes/demonstracao.py                # roteiro da aplicação em uso + capturas de tela
python testes/demonstracao.py --sem-gui      # somente o roteiro HTTP
```

| Arquivo | Testes | O que cobre |
|---|---|---|
| `testes/test_padroes.py` | 33 | O domínio, com um grupo de testes por padrão |
| `testes/test_servidor.py` | 35 | Os endpoints: formato das respostas, status HTTP e regras de negócio |
| `testes/test_cliente.py` | 12 | O acesso do cliente: rotas, erros HTTP, servidor fora do ar |
| `testes/test_cliente_gui.py` | 10 | A janela gráfica, com a plataforma `offscreen` do Qt |

Os testes do cliente conversam com o servidor real por meio de uma sessão que encaminha cada chamada ao `test_client` do Flask: o caminho completo é exercitado sem abrir porta de rede.

## Documentação

A documentação completa está em [`docs/DOCUMENTACAO.md`](docs/DOCUMENTACAO.md) e no PDF [`docs/Forum_Discussao_Design_Patterns.pdf`](docs/Forum_Discussao_Design_Patterns.pdf), com:

- requisitos funcionais e não-funcionais, e condições de aceitação;
- diagramas de classes do cliente e do servidor (`docs/imagens/`);
- a intenção de cada padrão e o problema que ele resolve no fórum;
- o código-fonte completo da aplicação;
- a demonstração da aplicação em uso, com a saída real de uma execução.

Para regerar documentação e diagramas após alterar o código:

```bash
python docs/gerar_diagramas.py
python docs/gerar_documentacao.py
```

O gerador reinsere o código-fonte real dos arquivos `.py` e executa a suíte de testes e o roteiro de demonstração na hora, então a documentação nunca mostra um resultado que o projeto não produz.

## Estrutura do projeto

```
forum-design-patterns/
├── servidor/        app.py (rotas Flask), __main__.py
├── cliente/         api.py (proxy), janela.py, dialogos.py, __main__.py
├── forum/           domínio: modelos, rastro, erros e os nove padrões
├── testes/          suíte automatizada e roteiro de demonstração
└── docs/            documentação, diagramas e geradores
```

## Decisões de projeto

- **O domínio não conhece Flask nem Qt.** `forum/` é Python puro e pode ser testado isoladamente; a fachada levanta `ErroDeForum` com o status HTTP adequado, e quem traduz isso em resposta é a camada de API.
- **O cliente não contém regra de negócio.** Toda validação acontece no servidor; a janela envia a requisição e trata a resposta.
- **Um padrão por módulo**, com intenção, aplicação e participantes documentados no cabeçalho do arquivo.
- **Rastro em vez de `print`.** O domínio registra o que cada padrão fez; o servidor devolve essas linhas na resposta e as grava no log.
