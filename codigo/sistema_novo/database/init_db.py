"""
init_db.py
==========
Script automatizado para inicializar e integrar o Banco de Dados PostgreSQL:
1. Conecta ao PostgreSQL utilizando as configurações do .env
2. Executa a estrutura DDL (database/estrutura_revisada.sql)
3. Registra os dados sintéticos DML (database/dados_revisada.sql)
4. Garante a conta de Administrador (admin@escola.com / admin123)
5. Executa o pipeline de Machine Learning (PCA / K-Means) gerando os dados de student_analytics
6. Atualiza os relatórios visuais na pasta static/relatorios
"""

import os
import sys
import shutil

# Garante saída UTF-8 no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt
from dotenv import load_dotenv

# Diretórios base
DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DB_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
STATIC_REPORTS_DIR = os.path.join(PROJECT_ROOT, "static", "relatorios")

# Carrega .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sistema")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_SCHEMA = os.getenv("DB_SCHEMA", "sc_student_diagnosis")


def ensure_database_exists():
    """Garante que o banco de dados exista no PostgreSQL antes de conectar."""
    try:
        root_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        root_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with root_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
            exists = cur.fetchone()
            if not exists:
                print(f"  ℹ Banco de dados '{DB_NAME}' não encontrado. Criando automaticamente...")
                cur.execute(f'CREATE DATABASE "{DB_NAME}";')
                print(f"  ✓ Banco de dados '{DB_NAME}' criado com sucesso.")
        root_conn.close()
    except Exception as e:
        print(f"  ℹ Aviso ao verificar existência do banco '{DB_NAME}': {e}")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options=f"-c search_path={DB_SCHEMA},public"
    )


def execute_sql_file(conn, filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def setup_database():
    print("=" * 70)
    print("INICIALIZAÇÃO E INTEGRAÇÃO DO BANCO DE DADOS POSTGRESQL (TCC)")
    print("=" * 70)
    
    ensure_database_exists()

    print(f"Conectando a {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME} (schema: {DB_SCHEMA})...")

    conn = get_connection()
    try:
        # 1. Estrutura revisada
        schema_file = os.path.join(DB_DIR, "estrutura_revisada.sql")
        print(f"\n[1/4] Aplicando estrutura revisada DDL ({os.path.basename(schema_file)})...")
        execute_sql_file(conn, schema_file)
        print("  ✓ Tabelas, esquemas, índices e triggers criados com sucesso.")

        # 2. Dados sintéticos revisados
        data_file = os.path.join(DB_DIR, "dados_revisada.sql")
        print(f"\n[2/4] Registrando dados sintéticos DML ({os.path.basename(data_file)})...")
        execute_sql_file(conn, data_file)
        print("  ✓ Usuários, turmas, alunos e diagnósticos sintéticos registrados.")

        # 3. Garantir administrador padrão
        print("\n[3/4] Verificando conta de Administrador Geral...")
        admin_pass_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (name_user, username, email, password, function)
                VALUES ('Administrador Geral', 'admin', 'admin@escola.com', %s, 'admin')
                ON CONFLICT (email) DO UPDATE SET
                    name_user = EXCLUDED.name_user,
                    username = EXCLUDED.username,
                    password = EXCLUDED.password,
                    function = 'admin';
            """, (admin_pass_hash,))
        conn.commit()
        print("  ✓ Admin configurado: admin@escola.com / admin123")

        # 4. Pipeline analítico (opcional caso o módulo externo esteja presente)
        analise_externa_dir = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "banco_de_dados_e_analise_de_dados", "analise_de_dados"))
        if os.path.exists(analise_externa_dir):
            try:
                print("\n[4/4] Executando pipeline analítico externo (K-Means, PCA e Indicadores)...")
                if analise_externa_dir not in sys.path:
                    sys.path.append(analise_externa_dir)
                from pipeline import run_pipeline
                df_analytics = run_pipeline()
                print(f"  ✓ Pipeline concluído: {len(df_analytics)} perfis processados.")

                os.makedirs(STATIC_REPORTS_DIR, exist_ok=True)
                for f in os.listdir(analise_externa_dir):
                    if f.endswith(".png") or f.endswith(".csv"):
                        shutil.copy2(os.path.join(analise_externa_dir, f), os.path.join(STATIC_REPORTS_DIR, f))
                print("  ✓ Relatórios visuais sincronizados em 'static/relatorios'.")
            except Exception as e:
                print(f"  ℹ Pipeline externo ignorado ({e}). Relatórios pré-existentes mantidos.")
        else:
            print("\n[4/4] Módulo de análise externa não anexado. Utilizando relatórios existentes em 'static/relatorios'.")

        # Resumo final
        print("\n" + "=" * 70)
        print("ESTATÍSTICAS ATUAIS DO BANCO DE DADOS:")
        print("=" * 70)
        tables = [
            "users", "teachers", "student", "diagnostic_requests",
            "diagnosis_answer", "socioeconomic_data", "cultural_context",
            "political_dimension", "school_experiences", "expectations_dreams",
            "student_analytics"
        ]
        with conn.cursor() as cur:
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                cnt = cur.fetchone()[0]
                print(f"  - {t:<25}: {cnt:>4} registros")
        print("=" * 70)
        print("Integração concluída com sucesso!")

    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
