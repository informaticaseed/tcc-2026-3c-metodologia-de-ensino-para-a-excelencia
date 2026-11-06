import os
import sys

# Garante que o diretório 'backend' esteja no sys.path mesmo ao executar da raiz
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import web

if __name__ == '__main__':
    print("Iniciando o servidor da plataforma EduMetodologias...")
    print("Acesse no navegador: http://127.0.0.1:5000")
    web.start_server()
