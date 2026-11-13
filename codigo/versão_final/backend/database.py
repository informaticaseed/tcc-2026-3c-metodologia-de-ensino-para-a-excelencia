import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


def get_connection():
    """Retorna uma conexão ativa com o PostgreSQL com search_path configurado."""
    schema = os.getenv("DB_SCHEMA")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        options=f"-c search_path={schema},public"
    )
    return conn