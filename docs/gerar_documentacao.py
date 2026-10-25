"""Gera a documentacao do projeto (Markdown e PDF).

O texto fica em docs/_fonte.md e usa tres marcadores, substituidos aqui:

    {{CODIGO:caminho}}  -> conteudo real do arquivo .py
    {{TESTES}}          -> saida de uma execucao da suite automatizada
    {{SAIDA}}           -> saida de uma execucao do roteiro de demonstracao

Como os dois ultimos sao executados na hora, a documentacao nunca mostra
um resultado que o projeto nao produz de fato.

Uso (a partir da raiz do repositorio):

    python docs/gerar_documentacao.py

Dependencias externas para o PDF: pandoc e wkhtmltopdf. Sem elas, apenas
o arquivo Markdown e gerado.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
FONTE = DOCS / "_fonte.md"
MARKDOWN = DOCS / "DOCUMENTACAO.md"
HTML = DOCS / "DOCUMENTACAO.html"
PDF = DOCS / "Forum_Discussao_Design_Patterns.pdf"
TITULO = "Forum de Discussao - Projeto de Design Patterns"


def executar(comando, descricao):
    """Roda um comando do proprio projeto e devolve a saida combinada."""
    print(f"Executando: {descricao}")
    resultado = subprocess.run(
        comando, cwd=RAIZ, capture_output=True, text=True,
        env={"PATH": __import__("os").environ.get("PATH", ""),
             "QT_QPA_PLATFORM": "offscreen",
             "HOME": __import__("os").environ.get("HOME", "")},
    )
    return (resultado.stdout + resultado.stderr).strip()


def bloco(texto, linguagem=""):
    return f"```{linguagem}\n{texto}\n```"


def expandir(texto):
    def substituir_codigo(correspondencia):
        caminho = RAIZ / correspondencia.group(1)
        return bloco(caminho.read_text(encoding="utf-8").rstrip(), "python")

    texto = re.sub(r"\{\{CODIGO:([^}]+)\}\}", substituir_codigo, texto)

    if "{{TESTES}}" in texto:
        saida = executar(
            [sys.executable, "-m", "unittest", "discover", "-s", "testes", "-v"],
            "suite de testes",
        )
        texto = texto.replace("{{TESTES}}", bloco(saida))

    if "{{SAIDA}}" in texto:
        saida = executar(
            [sys.executable, "testes/demonstracao.py", "--sem-gui"],
            "roteiro de demonstracao",
        )
        texto = texto.replace("{{SAIDA}}", bloco(saida))

    return texto


def gerar_markdown():
    MARKDOWN.write_text(expandir(FONTE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Markdown gerado: {MARKDOWN.relative_to(RAIZ)}")


def gerar_pdf():
    if not shutil.which("pandoc") or not shutil.which("wkhtmltopdf"):
        print("Aviso: pandoc e/ou wkhtmltopdf nao encontrados. PDF nao gerado.")
        return False

    subprocess.run(
        [
            "pandoc", str(MARKDOWN),
            "--standalone",
            "--resource-path", str(DOCS),
            "--css", str(DOCS / "estilo.css"),
            "--metadata", f"pagetitle={TITULO}",
            "--metadata", "lang=pt-BR",
            "-o", str(HTML),
        ],
        check=True,
    )
    subprocess.run(
        [
            "wkhtmltopdf",
            "--quiet",
            "--enable-local-file-access",
            "--page-size", "A4",
            "--margin-top", "16mm", "--margin-bottom", "16mm",
            "--margin-left", "14mm", "--margin-right", "14mm",
            str(HTML), str(PDF),
        ],
        check=True,
    )
    print(f"PDF gerado: {PDF.relative_to(RAIZ)}")
    return True


if __name__ == "__main__":
    gerar_markdown()
    sys.exit(0 if gerar_pdf() else 1)
