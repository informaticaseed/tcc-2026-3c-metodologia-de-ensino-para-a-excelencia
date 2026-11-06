"""
app.py
======
Ponto de entrada na raiz do projeto para facilidade de inicialização:
Execute diretamente: python app.py
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import web

if __name__ == '__main__':
    print("Iniciando o servidor da plataforma EduMetodologias...")
    print("Acesse no navegador: http://127.0.0.1:5000")
    web.start_server()

