import os                       #Acesso ao terminal do sistema
import psycopg                  #Driver do PostgreSQL
from dotenv import load_dotenv

load_dotenv()


def get_connection():                   #Lê dados de .env e conecta ao servidor.
    return psycopg.connect(
        host=os.getenv("DB_HOST"),          #IP do servidor
        port=os.getenv("DB_PORT"),          #Porta do Servidor
        dbname=os.getenv("DB_NAME"),        #Nome do BD
        user=os.getenv("DB_USER"),          #Nome do usuário
        password=os.getenv("DB_PASSWORD"),  #Senha do BD
    )