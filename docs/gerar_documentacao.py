"""Gera a documentacao do projeto (Markdown e PDF).

O texto fica em docs/_fonte.md e usa marcadores {{CODIGO:caminho}}. Este
script substitui cada marcador pelo conteudo real do arquivo .py, grava
docs/DOCUMENTACAO.md e converte o resultado em PDF.

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
TITULO = "Forum de Discussao - Padroes de Projeto em Python"


def expandir_codigo(texto):
    def substituir(correspondencia):
        caminho = RAIZ / correspondencia.group(1)
        conteudo = caminho.read_text(encoding="utf-8").rstrip()
        return f"```python\n{conteudo}\n```"

    return re.sub(r"\{\{CODIGO:([^}]+)\}\}", substituir, texto)


def gerar_markdown():
    markdown = expandir_codigo(FONTE.read_text(encoding="utf-8"))
    MARKDOWN.write_text(markdown, encoding="utf-8")
    print(f"Markdown gerado: {MARKDOWN.relative_to(RAIZ)}")
    return markdown


def gerar_pdf():
    if not shutil.which("pandoc") or not shutil.which("wkhtmltopdf"):
        print("Aviso: pandoc e/ou wkhtmltopdf nao encontrados. PDF nao gerado.")
        return False

    subprocess.run(
        [
            "pandoc", str(MARKDOWN),
            "--standalone",
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
