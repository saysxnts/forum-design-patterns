"""Ponto de entrada do servidor: python -m servidor"""

from .app import criar_app

ENDERECO = "127.0.0.1"
PORTA = 5000

if __name__ == "__main__":
    print(f"Servidor do forum em http://{ENDERECO}:{PORTA}")
    print("Pressione Ctrl+C para encerrar.")
    criar_app().run(host=ENDERECO, port=PORTA, debug=False)
