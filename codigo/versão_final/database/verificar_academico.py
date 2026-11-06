"""
verificar_academico.py
======================
Confere se os dados já gravados no PostgreSQL continuam compatíveis com as
séries e turmas definidas em ``backend/academico.py``.

Use este script depois de alterar a configuração acadêmica para descobrir
registros antigos que precisam ser migrados ou removidos:

    python database/verificar_academico.py

O script apenas diagnostica; ele não altera nenhum dado.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psycopg2
from dotenv import load_dotenv


DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DB_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from academico import SERIES_ENSINO_MEDIO_VALORES, TURMAS

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sistema")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_SCHEMA = os.getenv("DB_SCHEMA", "sc_student_diagnosis")

# Tabelas que guardam série/turma e precisam acompanhar a configuração.
TABELAS = (
    ("student", "estudantes"),
    ("diagnostic_requests", "pedidos de diagnóstico"),
    ("teacher_classes", "turmas de professores"),
)


def _formatar_valor(valor):
    """Deixa valores vazios visíveis na mensagem de erro."""
    if valor is None:
        return "<nulo>"
    if valor == "":
        return "<vazio>"
    return f'"{valor}"'


def verificar():
    """Retorna a lista de inconsistências encontradas no banco."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except psycopg2.Error as erro:
        print(f"Não foi possível conectar ao banco: {erro}")
        return None

    problemas = []

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SET search_path TO %s, public;",
                (DB_SCHEMA,),
            )

            print(f'Verificando o banco "{DB_NAME}"...')
            print(
                "Séries configuradas: "
                + ", ".join(SERIES_ENSINO_MEDIO_VALORES)
            )
            print("Turmas configuradas: " + ", ".join(TURMAS))
            print()

            for tabela, rotulo in TABELAS:
                try:
                    cur.execute(
                        f"SELECT DISTINCT grade, class FROM {tabela} "
                        "ORDER BY grade, class;"
                    )
                except psycopg2.errors.UndefinedTable:
                    conn.rollback()
                    problemas.append(
                        f"A tabela {tabela} não existe no schema {DB_SCHEMA}."
                    )
                    continue

                registros = cur.fetchall()

                for grade, turma in registros:
                    if grade not in SERIES_ENSINO_MEDIO_VALORES:
                        problemas.append(
                            f"{tabela} ({rotulo}): série "
                            f"{_formatar_valor(grade)} não configurada."
                        )

                    if turma not in TURMAS:
                        problemas.append(
                            f"{tabela} ({rotulo}): turma "
                            f"{_formatar_valor(turma)} não configurada."
                        )

                print(
                    f"  - {tabela}: {len(registros)} combinação(ões) "
                    "série/turma encontrada(s)."
                )
    finally:
        conn.close()

    return problemas


def main():
    problemas = verificar()

    if problemas is None:
        return 1

    if not problemas:
        print("\nTudo certo: nenhuma inconsistência acadêmica encontrada.")
        return 0

    print(f"\n{len(problemas)} inconsistência(s) encontrada(s):")
    for problema in problemas:
        print(f"  - {problema}")

    print(
        "\nAjuste os registros acima ou atualize backend/academico.py "
        "antes de usar o sistema."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
