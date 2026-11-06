"""
data_loader.py
==============
Módulo responsável pela ingestão de dados:
- Carregamento direto de CSV simulado (rápido e sem regex)
- Carregamento direto do PostgreSQL via psycopg2 / pandas
- Leitura de contingência de arquivo SQL
- Exportação e persistência dos resultados analíticos
"""

import os
import re
import pandas as pd
from config import (
    USE_POSTGRESQL_DB,
    DB_CONFIG,
    DEFAULT_SIMULATED_CSV,
    POSTGRESQL_DIR,
    SQL_ANALYTICS_PATH
)
import psycopg2


def split_sql_values(values_str):
    """Divide valores SQL respeitando strings com aspas e booleanos/números."""
    pattern = re.compile(r"""(?:'([^']*(?:''[^']*)*)'|([^,]+))""")
    tokens = []
    for match in pattern.finditer(values_str):
        str_val, other_val = match.groups()
        if str_val is not None:
            tokens.append(str_val.replace("''", "'"))
        elif other_val is not None:
            clean = other_val.strip()
            if clean.upper() == 'TRUE':
                tokens.append(True)
            elif clean.upper() == 'FALSE':
                tokens.append(False)
            elif clean.upper() == 'NULL':
                tokens.append(None)
            else:
                try:
                    tokens.append(float(clean) if '.' in clean else int(clean))
                except ValueError:
                    tokens.append(clean)
    return tokens


def load_data_from_csv(csv_path=DEFAULT_SIMULATED_CSV):
    """Carrega os dados diretamente de arquivo CSV limpo (método mais rápido)."""
    print(f"Lendo dados diretamente do CSV: {csv_path}")
    df = pd.read_csv(csv_path, encoding="utf-8")
    print(f"Total de estudantes carregados com sucesso: {len(df)}")
    return df


def split_sql_rows(values_block):
    """
    Divide o bloco VALUES em linhas, respeitando parênteses aninhados
    (subconsultas) e strings entre aspas simples.
    """
    rows = []
    current = []
    depth = 0
    in_quote = False
    i = 0

    while i < len(values_block):
        char = values_block[i]

        if in_quote:
            current.append(char)
            if char == "'":
                # Aspas escapadas dentro de string SQL ('')
                if i + 1 < len(values_block) and values_block[i + 1] == "'":
                    current.append(values_block[i + 1])
                    i += 1
                else:
                    in_quote = False
        elif char == "'":
            in_quote = True
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            rows.append("".join(current).strip())
            current = []
        else:
            current.append(char)

        i += 1

    tail = "".join(current).strip()
    if tail:
        rows.append(tail)

    return [row for row in rows if row]


def split_sql_row_fields(row):
    """Divide uma linha VALUES em campos no nível superior."""
    fields = []
    current = []
    depth = 0
    in_quote = False
    i = 0
    row = row.strip()

    if row.startswith("(") and row.endswith(")"):
        row = row[1:-1]

    while i < len(row):
        char = row[i]

        if in_quote:
            current.append(char)
            if char == "'":
                if i + 1 < len(row) and row[i + 1] == "'":
                    current.append(row[i + 1])
                    i += 1
                else:
                    in_quote = False
        elif char == "'":
            in_quote = True
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            fields.append("".join(current).strip())
            current = []
        else:
            current.append(char)

        i += 1

    tail = "".join(current).strip()
    if tail:
        fields.append(tail)

    return fields


def parse_sql_scalar(value):
    """Converte um campo SQL em valor Python."""
    value = value.strip()

    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")

    upper = value.upper()

    if upper == "TRUE":
        return True
    if upper == "FALSE":
        return False
    if upper == "NULL":
        return None

    # Subconsultas e expressões SQL são mantidas como texto.
    if value.startswith("(") or value.endswith(")"):
        return value

    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def extract_insert_rows(content, table_name):
    """Retorna as linhas de um bloco INSERT ... VALUES da tabela indicada."""
    block = re.search(
        rf"INSERT\s+INTO\s+{table_name}\b[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)",
        content,
        re.IGNORECASE
    )

    if not block:
        return []

    return split_sql_rows(block.group(1))


def load_data_from_sql_file(sql_path=None):
    """
    Lê dados extraindo os blocos INSERT do arquivo SQL (fallback).

    O parser aceita o formato atual, baseado em e-mail:
      student (user_id, school_id, full_name, email, grade, class)
      socioeconomic_data (answer_id, ...)
    em que as chaves estrangeiras são subconsultas SELECT.
    """
    if sql_path is None:
        sql_path = os.path.join(POSTGRESQL_DIR, "dados_revisada.sql")
        if not os.path.exists(sql_path):
            sql_path = os.path.join(POSTGRESQL_DIR, "dados.sql")

    print(f"Lendo dados diretamente do arquivo SQL:\n -> {sql_path}")
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"Arquivo SQL não encontrado em: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()

    students_data = {}

    for row in extract_insert_rows(content, "(?:students?|alunos)"):
        raw_fields = split_sql_row_fields(row)

        # O e-mail é o primeiro literal entre aspas que contém "@".
        # Subconsultas podem conter e-mails e não devem ser confundidas.
        email_index = next(
            (
                index for index, raw in enumerate(raw_fields)
                if raw.startswith("'") and raw.endswith("'") and "@" in raw
            ),
            None
        )

        # O nome completo fica imediatamente antes do e-mail.
        if email_index is None or email_index < 1:
            continue

        fields = [parse_sql_scalar(field) for field in raw_fields]
        email = fields[email_index]
        remaining = fields[email_index + 1:]

        students_data[email] = {
            "full_name": fields[email_index - 1],
            "email": email,
            "grade": remaining[0] if len(remaining) > 0 else None,
            "school_class": remaining[1] if len(remaining) > 1 else None
        }

    def process_table(table_name, column_names):
        for row in extract_insert_rows(content, table_name):
            fields = [parse_sql_scalar(field) for field in split_sql_row_fields(row)]

            if len(fields) < 2:
                continue

            email_match = re.search(
                r"email\s*=\s*'([^']+)'",
                str(fields[0]),
                re.IGNORECASE
            )

            if not email_match:
                continue

            email = email_match.group(1)

            if email not in students_data:
                students_data[email] = {"email": email}

            for column, value in zip(column_names, fields[1:]):
                students_data[email][column] = value

    process_table("socioeconomic_data", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("dados_socioeconomicos", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("cultural_context", ["cultural_activities", "community_tradition", "family_role"])
    process_table("contexto_cultural", ["cultural_activities", "community_tradition", "family_role"])
    process_table("school_experiences", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("experiencias_escolares", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("expectations_dreams", ["personal_professional_goals", "school_support"])
    process_table("expectativas_sonhos", ["personal_professional_goals", "school_support"])

    process_table("socioeconomic_data", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("dados_socioeconomicos", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("cultural_context", ["cultural_activities", "community_tradition", "family_role"])
    process_table("contexto_cultural", ["cultural_activities", "community_tradition", "family_role"])
    process_table("school_experiences", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("experiencias_escolares", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("expectations_dreams", ["personal_professional_goals", "school_support"])
    process_table("expectativas_sonhos", ["personal_professional_goals", "school_support"])

    df = pd.DataFrame(list(students_data.values()))
    print(f"Total de estudantes carregados com sucesso: {len(df)}")
    return df


def load_data_from_database(config=DB_CONFIG, order_id=None):
    """
    Carrega os dados diretamente do banco de dados PostgreSQL.

    Quando ``order_id`` é informado, retorna somente as respostas do
    pedido de diagnóstico correspondente. Sem filtro, mantém o
    comportamento global usado pelo pipeline para popular
    ``student_analytics``.
    """
    if psycopg2 is None:
        raise ImportError("A biblioteca 'psycopg2' não está instalada. Execute: pip install psycopg2-binary")

    conn = psycopg2.connect(
        host=config["host"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        port=config.get("port", 5432),
        options=config["options"]
    )

    # Identifica nome da tabela de estudantes (student ou students)
    #cur = conn.cursor()
    #cur.execute("""
    #    SELECT table_name FROM information_schema.tables 
    #    WHERE table_schema = 'sc_student_diagnosis' 
    #      AND table_name IN ('student', 'students', 'alunos')
    #    LIMIT 1;
    #""")
    #res = cur.fetchone()
    #student_table = res[0] if res else "student"
    #cur.close()

    student_table = "student"

    order_filter = ""
    params = None

    if order_id is not None:
        order_filter = "WHERE da.order_id = %s"
        params = (int(order_id),)

    query = f"""
    SELECT 
        da.id AS answer_id,
        s.id AS student_id,
        s.full_name AS full_name,
        s.email,
        s.grade AS grade,
        s.class AS school_class,
        se.family_income AS family_income,
        se.works_besides_studying AS works_besides_studying,
        se.work_hours_per_week AS work_hours,
        se.parents_education AS parents_education,
        se.has_internet_at_home AS has_internet,
        se.has_computer_at_home AS has_computer,
        exp.opinion_is_heard_at_school AS opinion_is_heard,
        exp.teachers_relations AS teachers_relations,
        exp.learning_difficulties AS learning_difficulties,
        ed.personal_professional_goals AS personal_professional_goals,
        ed.support_that_the_school_should_offer AS school_support,
        cc.cultural_activities AS cultural_activities,
        cc.community_cultural_tradition AS community_tradition,
        cc.role_family_community_training AS family_role
    FROM {student_table} s
    JOIN diagnosis_answer da ON da.student_id = s.id
    LEFT JOIN socioeconomic_data se ON se.answer_id = da.id
    LEFT JOIN school_experiences exp ON exp.answer_id = da.id
    LEFT JOIN expectations_dreams ed ON ed.answer_id = da.id
    LEFT JOIN cultural_context cc ON cc.answer_id = da.id
    {order_filter}
    ORDER BY s.grade, s.class, s.full_name;
    """
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def load_dataset(order_id=None):
    """Função unificada de carregamento com seleção inteligente de fonte."""
    if USE_POSTGRESQL_DB:
        print("Conectando ao banco de dados PostgreSQL...")
        return load_data_from_database(DB_CONFIG, order_id=order_id)
    if os.path.exists(DEFAULT_SIMULATED_CSV):
        return load_data_from_csv(DEFAULT_SIMULATED_CSV)
    return load_data_from_sql_file()


def export_analytics_to_sql(df, output_path=SQL_ANALYTICS_PATH):
    """
    Gera script SQL offline para persistência na tabela student_analytics.

    A estratégia é idempotente sem consumir a sequence da coluna identity:
    1. UPDATE nas respostas que já possuem analytics;
    2. INSERT ... SELECT ... WHERE NOT EXISTS apenas para as novas.
    """
    lines = [
        "-- inserts_student_analytics.sql",
        "-- Script gerado automaticamente pelo pipeline de análise de dados (analise_de_dados.py)",
        "-- Persiste os indicadores calculados e o perfil de Machine Learning (K-Means/PCA)",
        "--",
        "-- Estratégia idempotente: atualiza as linhas existentes e insere apenas",
        "-- as respostas que ainda não possuem analytics. Assim a sequence da",
        "-- coluna identity não é consumida em execuções repetidas.",
        "",
        "SET search_path TO sc_student_diagnosis, public;",
        "",
        "-- 1) Atualiza registros já existentes (não consome identity).",
    ]

    value_rows = []
    update_rows = []

    for _, row in df.iterrows():
        email = str(row.get('email', '')).replace("'", "''")
        ped_profile = str(row.get('pedagogical_profile', '')).replace("'", "''")
        pca_1 = float(row.get('pca_1', 0.0))
        pca_2 = float(row.get('pca_2', 0.0))

        ans_subquery = (
            f"    (SELECT da.id FROM diagnosis_answer da\n"
            f"     JOIN student s ON da.student_id = s.id\n"
            f"     WHERE s.email = '{email}' LIMIT 1)"
        )

        value_rows.append(
            f"  (\n"
            f"{ans_subquery},\n"
            f"    {row['idx_socioeconomic_digital']:.2f}, {row['idx_work_overload']:.2f}, "
            f"{row['idx_school_bonding']:.2f}, {row['idx_cultural_capital']:.2f},\n"
            f"    {int(row['cluster'])}, '{ped_profile}', {pca_1:.3f}, {pca_2:.3f}\n"
            f"  )"
        )

        update_rows.append(
            "UPDATE student_analytics SET\n"
            f"  idx_socioeconomic_digital = {row['idx_socioeconomic_digital']:.2f},\n"
            f"  idx_work_overload = {row['idx_work_overload']:.2f},\n"
            f"  idx_school_bonding = {row['idx_school_bonding']:.2f},\n"
            f"  idx_cultural_capital = {row['idx_cultural_capital']:.2f},\n"
            f"  cluster_id = {int(row['cluster'])},\n"
            f"  pedagogical_profile = '{ped_profile}',\n"
            f"  pca_1 = {pca_1:.3f},\n"
            f"  pca_2 = {pca_2:.3f},\n"
            f"  updated_at = NOW()\n"
            f"WHERE answer_id = {ans_subquery};"
        )

    lines.append("\n\n".join(update_rows))
    lines.append("")
    lines.append("-- 2) Insere somente respostas que ainda não possuem analytics.")
    lines.append("INSERT INTO student_analytics (")
    lines.append("  answer_id,")
    lines.append("  idx_socioeconomic_digital,")
    lines.append("  idx_work_overload,")
    lines.append("  idx_school_bonding,")
    lines.append("  idx_cultural_capital,")
    lines.append("  cluster_id,")
    lines.append("  pedagogical_profile,")
    lines.append("  pca_1,")
    lines.append("  pca_2")
    lines.append(")")
    lines.append("SELECT")
    lines.append("  novos.answer_id,")
    lines.append("  novos.idx_socioeconomic_digital,")
    lines.append("  novos.idx_work_overload,")
    lines.append("  novos.idx_school_bonding,")
    lines.append("  novos.idx_cultural_capital,")
    lines.append("  novos.cluster_id,")
    lines.append("  novos.pedagogical_profile,")
    lines.append("  novos.pca_1,")
    lines.append("  novos.pca_2")
    lines.append("FROM (")
    lines.append("  VALUES")
    lines.append(",\n".join(value_rows))
    lines.append(") AS novos (answer_id, idx_socioeconomic_digital, idx_work_overload, idx_school_bonding, idx_cultural_capital, cluster_id, pedagogical_profile, pca_1, pca_2)")
    lines.append("WHERE NOT EXISTS (")
    lines.append("  SELECT 1")
    lines.append("  FROM student_analytics AS existente")
    lines.append("  WHERE existente.answer_id = novos.answer_id")
    lines.append(");\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Script SQL analítico exportado para: {output_path}")


def save_analytics_to_database(df, config=DB_CONFIG):
    """Salva diretamente na tabela student_analytics via PostgreSQL."""
    if psycopg2 is None:
        print("Aviso: 'psycopg2' não instalado. Não foi possível persistir diretamente no PostgreSQL.")
        return

    try:
        conn = psycopg2.connect(**config)
        cur = conn.cursor()

        # Atualiza primeiro e só insere quando ainda não existe. Isso mantém
        # o pipeline idempotente sem consumir a sequence de student_analytics
        # em execuções repetidas (ON CONFLICT consumiria um ID por tentativa).
        update_query = """
        UPDATE student_analytics SET
            idx_socioeconomic_digital = %s,
            idx_work_overload = %s,
            idx_school_bonding = %s,
            idx_cultural_capital = %s,
            cluster_id = %s,
            pedagogical_profile = %s,
            pca_1 = %s,
            pca_2 = %s,
            updated_at = NOW()
        WHERE answer_id = %s;
        """
        insert_query = """
        INSERT INTO student_analytics (
            answer_id, idx_socioeconomic_digital, idx_work_overload, idx_school_bonding,
            idx_cultural_capital, cluster_id, pedagogical_profile,
            pca_1, pca_2, updated_at
        )
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1
            FROM student_analytics
            WHERE answer_id = %s
        );
        """
        saved = 0
        for _, row in df.iterrows():
            ans_id = row.get('answer_id')

            if ans_id is None or pd.isna(ans_id):
                raise ValueError(
                f"Resultado sem answer_id. "
                f"Não é possível associá-lo com segurança ao diagnóstico: "
                f"{row.get('full_name', 'Estudante desconhecido')}"
            )
            ans_id = int(ans_id)

            valores = (
                float(row['idx_socioeconomic_digital']), float(row['idx_work_overload']),
                float(row['idx_school_bonding']), float(row['idx_cultural_capital']),
                int(row['cluster']), str(row['pedagogical_profile']),
                float(row.get('pca_1', 0.0)), float(row.get('pca_2', 0.0))
            )

            cur.execute(update_query, (*valores, ans_id))

            if cur.rowcount == 0:
                cur.execute(insert_query, (ans_id, *valores, ans_id))

            saved += 1
        conn.commit()
        cur.close()
        conn.close()
        print(f"Total de {saved} registros gravados em 'student_analytics' com sucesso!")
    except Exception as e:
        print(f"Erro ao gravar resultados analíticos no PostgreSQL: {e}")
