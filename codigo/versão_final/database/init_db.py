
"""
init_db.py
==========
Inicialização automatizada do PostgreSQL.

Responsabilidades:
1. Verificar e criar o banco, se necessário.
2. Executar a estrutura DDL.
3. Criar a tabela de controle das migrações.
4. Inserir os dados iniciais.
5. Executar somente as migrações pendentes.
6. Garantir a conta de superadministrador sem redefinir sua senha.
7. Executar o pipeline de Machine Learning.
8. Atualizar os relatórios visuais.
"""

import os
import sys

# Garante saída UTF-8 no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt
from dotenv import load_dotenv


# ============================================================
# 1. CONFIGURAÇÕES E DIRETÓRIOS
# ============================================================

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DB_DIR)

BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
PROTECTED_REPORTS_DIR = os.path.join(
    BACKEND_DIR, "relatorios_globais"
)

MIGRATIONS_DIR = os.path.join(DB_DIR, "migrations")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sistema")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_SCHEMA = os.getenv("DB_SCHEMA", "sc_student_diagnosis")


# ============================================================
# 2. CONEXÃO COM O POSTGRESQL
# ============================================================

def ensure_database_exists():
    """Cria o banco de dados caso ele ainda não exista."""

    root_conn = None

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
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s;",
                (DB_NAME,)
            )

            if not cur.fetchone():
                print(
                    f"Banco '{DB_NAME}' não encontrado. Criando..."
                )

                # O nome do banco é delimitado por aspas.
                cur.execute(
                    psycopg2.sql.SQL(
                        'CREATE DATABASE {}'
                    ).format(
                        sql.Identifier(DB_NAME)
                    )
                )

                print("Banco criado com sucesso.")

    except Exception as e:
        raise RuntimeError(
            f"Não foi possível verificar/criar o banco: {e}"
        ) from e

    finally:
        if root_conn:
            root_conn.close()


def get_connection():
    """Abre uma conexão usando o schema configurado."""

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options=f"-c search_path={DB_SCHEMA},public"
    )


# ============================================================
# 3. EXECUÇÃO DE ARQUIVOS SQL
# ============================================================

def execute_sql_file(conn, filepath):
    """Executa um arquivo SQL e confirma a transação."""

    if not os.path.isfile(filepath):
        raise FileNotFoundError(
            f"Arquivo SQL não encontrado: {filepath}"
        )

    with open(filepath, "r", encoding="utf-8") as file:
        sql = file.read()

    try:
        with conn.cursor() as cur:
            cur.execute(sql)

        conn.commit()

    except Exception:
        conn.rollback()
        raise


# ============================================================
# 4. CONTROLE DAS MIGRAÇÕES
# ============================================================

def setup_migration_table(conn):
    """
    Cria a tabela que registra as migrações já executadas.
    Deve ser chamada depois da criação do schema.
    """

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(100) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

        conn.commit()
        print("Tabela de controle das migrações preparada.")

    except Exception:
        conn.rollback()
        raise


def run_migrations(conn):
    """
    Procura arquivos SQL na pasta migrations.
    Executa somente aqueles que ainda não foram registrados.
    """

    if not os.path.isdir(MIGRATIONS_DIR):
        print("Pasta de migrações não encontrada. Nenhuma migração executada.")
        return

    migration_files = sorted(
        file_name
        for file_name in os.listdir(MIGRATIONS_DIR)
        if file_name.endswith(".sql")
    )

    if not migration_files:
        print("Nenhuma migração encontrada.")
        return

    print("\nVerificando migrações pendentes...")

    for file_name in migration_files:

        # A versão será o nome do arquivo sem a extensão.
        # Exemplo: 001_perfis_administrativos
        version = os.path.splitext(file_name)[0]

        filepath = os.path.join(MIGRATIONS_DIR, file_name)

        try:
            with conn.cursor() as cur:

                # Verifica se a migração já foi aplicada.
                cur.execute("""
                    SELECT 1
                    FROM schema_migrations
                    WHERE version = %s;
                """, (version,))

                already_applied = cur.fetchone()

                if already_applied:
                    print(f"  Já aplicada: {version}")
                    continue

                print(f"  Executando: {version}")

                # Lê e executa o arquivo SQL.
                with open(filepath, "r", encoding="utf-8") as file:
                    sql = file.read()

                cur.execute(sql)

                # Registra a migração na mesma transação.
                cur.execute("""
                    INSERT INTO schema_migrations (version)
                    VALUES (%s);
                """, (version,))

            # Só registra definitivamente se tudo funcionar.
            conn.commit()

            print(f"  Migração concluída: {version}")

        except Exception as e:
            conn.rollback()

            raise RuntimeError(
                f"Falha ao executar a migração {version}: {e}"
            ) from e

# ============================================================
# 5. CORRIGIR SENHAS DAS CONTAS DE DEMONSTRAÇÃO
# ============================================================

def corrigir_senhas_demo(conn):
    """
    Substitui senhas fictícias por hashes bcrypt válidos.
    Preserva senhas NULL e senhas já modificadas.
    """

    senha_inicial = "Teste@2026"

    senhas_ficticias = [
        "hash_prof",
        "hash_aluno",
        "hash_admin"
    ]

    try:
        with conn.cursor() as cur:

            # Localiza somente usuários com senhas fictícias.
            cur.execute(
                """
                SELECT id
                FROM users
                WHERE password = ANY(%s);
                """,
                (senhas_ficticias,)
            )

            usuarios = cur.fetchall()

            # Gera um hash individual para cada usuário.
            for (user_id,) in usuarios:

                senha_hash = bcrypt.hashpw(
                    senha_inicial.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                cur.execute(
                    """
                    UPDATE users
                    SET password = %s
                    WHERE id = %s
                      AND password = ANY(%s);
                    """,
                    (senha_hash, user_id, senhas_ficticias)
                )

        conn.commit()

        print(
            f"[OK] {len(usuarios)} contas de demonstração "
            "receberam hashes bcrypt."
        )

    except Exception:
        conn.rollback()
        raise


# ============================================================
# 5. GARANTIR SUPERADMINISTRADOR
# ============================================================

def ensure_superadmin(conn):
    """
    Cria a conta principal caso ela não exista.
    Não altera senha ou perfil de uma conta já existente.
    """

    print("\nVerificando conta de superadministrador...")

    password_hash = bcrypt.hashpw(
        "admin123".encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (
                    username,
                    email,
                    password,
                    function,
                    school_id,
                    is_active
                )
                VALUES (
                    'admin',
                    'admin@escola.com',
                    %s,
                    'superadmin',
                    NULL,
                    TRUE
                )
                ON CONFLICT (email) DO NOTHING;
            """, (password_hash,))

            created = cur.rowcount

        conn.commit()

        if created:
            print(
                "Superadministrador criado: "
                "admin@escola.com / admin123"
            )
        else:
            print(
                "Conta admin@escola.com já existente. "
                "Senha e perfil preservados."
            )

    except Exception:
        conn.rollback()
        raise


# ============================================================
# 6. PIPELINE DE MACHINE LEARNING
# ============================================================

def run_analytics_pipeline():
    """Executa o pipeline; os relatórios ficam em diretório protegido."""

    analise_externa_dir = os.path.join(
        BACKEND_DIR, "analise_de_dados"
    )

    if not os.path.isdir(analise_externa_dir):
        print(
            "\nMódulo de análise externa não encontrado. "
            "Relatórios existentes serão mantidos."
        )
        return

    try:
        print(
            "\nExecutando pipeline analítico "
            "(K-Means, PCA e indicadores)..."
        )

        if analise_externa_dir not in sys.path:
            sys.path.append(analise_externa_dir)

        from pipeline import run_pipeline

        df_analytics = run_pipeline()

        print(
            f"Pipeline concluído: "
            f"{len(df_analytics)} perfis processados."
        )

        os.makedirs(PROTECTED_REPORTS_DIR, exist_ok=True)

        print(
            "Relatórios globais gravados em diretório protegido "
            "(backend/relatorios_globais)."
        )

    except Exception as e:
        print(
            f"Pipeline não concluído: {e}. "
            "Relatórios anteriores foram mantidos."
        )


# ============================================================
# 7. RESUMO DO BANCO DE DADOS
# ============================================================

def show_database_statistics(conn):
    """Exibe a quantidade de registros das principais tabelas."""

    print("\n" + "=" * 70)
    print("ESTATÍSTICAS ATUAIS DO BANCO DE DADOS")
    print("=" * 70)

    tables = [
        "users",
        "teachers",
        "student",
        "diagnostic_requests",
        "diagnosis_answer",
        "socioeconomic_data",
        "cultural_context",
        "school_experiences",
        "expectations_dreams",
        "student_analytics"
    ]

    with conn.cursor() as cur:

        for table in tables:

            cur.execute(
                f"SELECT COUNT(*) FROM {table};"
            )

            count = cur.fetchone()[0]

            print(f"  - {table:<25}: {count:>4} registros")

    print("=" * 70)


# ============================================================
# 8. INICIALIZAÇÃO PRINCIPAL
# ============================================================

def setup_database():

    print("=" * 70)
    print("INICIALIZAÇÃO DO BANCO DE DADOS POSTGRESQL (TCC)")
    print("=" * 70)

    ensure_database_exists()

    print(
        f"\nConectando a {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME} "
        f"(schema: {DB_SCHEMA})..."
    )

    conn = get_connection()

    try:

        # ETAPA 1 - Estrutura DDL
        schema_file = os.path.join(
            DB_DIR, "estrutura_revisada.sql"
        )

        print("\n[1/6] Aplicando estrutura do banco...")
        execute_sql_file(conn, schema_file)

        print("Estrutura aplicada com sucesso.")

        # ETAPA 2 - Controle de migrações
        print("\n[2/6] Preparando controle de migrações...")
        setup_migration_table(conn)

        # ETAPA 3 - Migrações
        print("\n[3/6] Verificando atualizações do banco...")
        run_migrations(conn)

        # ETAPA 4 - Dados iniciais
        data_file = os.path.join(
            DB_DIR, "dados_revisada.sql"
        )

        print("\n[4/6] Registrando dados iniciais...")
        execute_sql_file(conn, data_file)

        print("Dados iniciais processados.")

        # Corrigir senhas fictícias das contas de demonstração
        print("\nCorrigindo senhas das contas de demonstração...")
        corrigir_senhas_demo(conn)

        # ETAPA 5 - Superadministrador
        print("\n[5/6] Verificando superadministrador...")
        ensure_superadmin(conn)

        # ETAPA 6 - Pipeline analítico
        print("\n[6/6] Atualizando análise de dados...")
        run_analytics_pipeline()

        # Resumo
        show_database_statistics(conn)

        print("\nInicialização concluída com sucesso!")

    except Exception as e:

        print("\nERRO DURANTE A INICIALIZAÇÃO:")
        print(e)

        raise

    finally:
        conn.close()


# ============================================================
# 9. EXECUÇÃO DO SCRIPT
# ============================================================

if __name__ == "__main__":
    setup_database()
