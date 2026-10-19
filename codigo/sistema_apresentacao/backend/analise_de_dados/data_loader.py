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

try:
    from .config import (
        USE_POSTGRESQL_DB,
        DB_CONFIG,
        DEFAULT_SIMULATED_CSV,
        POSTGRESQL_DIR,
        SQL_ANALYTICS_PATH
    )
except (ImportError, ValueError):
    from config import (
        USE_POSTGRESQL_DB,
        DB_CONFIG,
        DEFAULT_SIMULATED_CSV,
        POSTGRESQL_DIR,
        SQL_ANALYTICS_PATH
    )

try:
    import psycopg2
except ImportError:
    psycopg2 = None


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


def load_data_from_sql_file(sql_path=None):
    """Lê dados extraindo os blocos INSERT do arquivo SQL (fallback)."""
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
    students_pattern = re.compile(
        r"\(\s*(?:\(SELECT\b[\s\S]*?email\s*=\s*'([^']+)'[\s\S]*?\)|NULL|\d+)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
        re.IGNORECASE
    )

    students_block = re.search(
        r"INSERT\s+INTO\s+(?:students?|alunos)[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)", 
        content, 
        re.IGNORECASE
    )
    if students_block:
        for match in students_pattern.finditer(students_block.group(1)):
            email_ref = match.group(1)
            remainder = match.group(2)
            parsed_values = split_sql_values(remainder)
            if len(parsed_values) >= 4:
                email_key = parsed_values[1] if parsed_values[1] else email_ref
                students_data[email_key] = {
                    "full_name": parsed_values[0],
                    "email": email_key,
                    "grade": parsed_values[2],
                    "school_class": parsed_values[3]
                }

    dimension_pattern = re.compile(
        r"\(\s*\(SELECT\b[\s\S]*?(?:[a-zA-Z0-9_]+\.)?email\s*=\s*'([^']+)'[\s\S]*?\)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
        re.IGNORECASE
    )

    def process_table(table_name, column_names):
        block = re.search(
            rf"INSERT\s+INTO\s+{table_name}[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)", 
            content, 
            re.IGNORECASE
        )
        if not block:
            return
        for match in dimension_pattern.finditer(block.group(1)):
            email = match.group(1)
            parsed_values = split_sql_values(match.group(2))
            if email not in students_data:
                students_data[email] = {"email": email}
            for col, val in zip(column_names, parsed_values):
                students_data[email][col] = val

    process_table("socioeconomic_data", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("dados_socioeconomicos", ["family_income", "works_besides_studying", "work_hours", "parents_education", "has_internet", "has_computer"])
    process_table("cultural_context", ["cultural_activities", "community_tradition", "family_role"])
    process_table("contexto_cultural", ["cultural_activities", "community_tradition", "family_role"])
    process_table("political_dimension", ["follows_politics", "participated_in_social_movement", "education_role"])
    process_table("dimensao_politica", ["follows_politics", "participated_in_social_movement", "education_role"])
    process_table("school_experiences", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("experiencias_escolares", ["teachers_relations", "opinion_is_heard", "learning_difficulties"])
    process_table("expectations_dreams", ["personal_professional_goals", "school_support"])
    process_table("expectativas_sonhos", ["personal_professional_goals", "school_support"])

    df = pd.DataFrame(list(students_data.values()))
    print(f"Total de estudantes carregados com sucesso: {len(df)}")
    return df


def load_data_from_database(config=DB_CONFIG):
    """Carrega os dados diretamente do banco de dados PostgreSQL."""
    if psycopg2 is None:
        raise ImportError("A biblioteca 'psycopg2' não está instalada. Execute: pip install psycopg2-binary")

    conn = psycopg2.connect(
        host=config["host"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        port=config.get("port", 5432)
    )

    # Identifica nome da tabela de estudantes (student ou students)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'sc_student_diagnosis' 
          AND table_name IN ('student', 'students', 'alunos')
        LIMIT 1;
    """)
    res = cur.fetchone()
    student_table = res[0] if res else "student"
    cur.close()

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
        COALESCE(se.work_hours_per_week, se.horas_trabalho_semana) AS work_hours,
        COALESCE(se.parents_education, se.escolaridade_pais_responsaveis) AS parents_education,
        COALESCE(se.has_internet_at_home, se.tem_internet_casa) AS has_internet,
        COALESCE(se.has_computer_at_home, se.tem_computador_casa) AS has_computer,
        COALESCE(exp.opinion_is_heard_at_school, exp.opiniao_e_ouvida_na_escola) AS opinion_is_heard,
        COALESCE(exp.teachers_relations, exp.relacao_professores) AS teachers_relations,
        COALESCE(exp.learning_difficulties, exp.dificuldades_aprendizado) AS learning_difficulties,
        COALESCE(ed.personal_professional_goals, ed.objetivos_pessoais_profissionais) AS personal_professional_goals,
        COALESCE(ed.support_that_the_school_should_offer, ed.apoio_que_a_escola_deveria_oferecer) AS school_support,
        COALESCE(cc.cultural_activities, cc.atividades_culturais) AS cultural_activities,
        COALESCE(cc.community_cultural_tradition, cc.tradicao_cultural_comunitaria) AS community_tradition,
        COALESCE(cc.role_family_community_training, cc.papel_familia_comunidade_formacao) AS family_role,
        COALESCE(pol.follows_politics_society_news, pol.acompanha_noticias_politica_sociedade) AS follows_politics,
        COALESCE(pol.participated_in_social_movement, pol.participou_movimento_social) AS participated_in_social_movement,
        COALESCE(pol.role_education_social_transformation, pol.papel_educacao_transformacao_social) AS education_role
    FROM {student_table} s
    JOIN diagnosis_answer da ON da.student_id = s.id
    LEFT JOIN socioeconomic_data se ON se.answer_id = da.id
    LEFT JOIN school_experiences exp ON exp.answer_id = da.id
    LEFT JOIN expectations_dreams ed ON ed.answer_id = da.id
    LEFT JOIN cultural_context cc ON cc.answer_id = da.id
    LEFT JOIN political_dimension pol ON pol.answer_id = da.id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def load_dataset():
    """Função unificada de carregamento com seleção inteligente de fonte."""
    if USE_POSTGRESQL_DB:
        print("Conectando ao banco de dados PostgreSQL...")
        return load_data_from_database(DB_CONFIG)
    if os.path.exists(DEFAULT_SIMULATED_CSV):
        return load_data_from_csv(DEFAULT_SIMULATED_CSV)
    return load_data_from_sql_file()


def export_analytics_to_sql(df, output_path=SQL_ANALYTICS_PATH):
    """Gera script SQL offline para persistência na tabela student_analytics."""
    lines = [
        "-- inserts_student_analytics.sql",
        "-- Script gerado automaticamente pelo pipeline de análise de dados (analise_de_dados.py)",
        "-- Persiste os indicadores calculados e o perfil de Machine Learning (K-Means/PCA)",
        "",
        "SET search_path TO sc_student_diagnosis, sc_diagnostico_estudantil, public;",
        "",
        "INSERT INTO student_analytics (",
        "  answer_id,",
        "  idx_socioeconomic_digital,",
        "  idx_work_overload,",
        "  idx_school_bonding,",
        "  idx_political_engagement,",
        "  idx_cultural_capital,",
        "  cluster_id,",
        "  pedagogical_profile,",
        "  pca_1,",
        "  pca_2",
        ")",
        "VALUES"
    ]

    value_rows = []
    for _, row in df.iterrows():
        email = str(row.get('email', '')).replace("'", "''")
        ped_profile = str(row.get('pedagogical_profile', '')).replace("'", "''")
        pca_1 = float(row.get('pca_1', 0.0))
        pca_2 = float(row.get('pca_2', 0.0))

        ans_subquery = (
            f"    (SELECT da.id FROM diagnosis_answer da\n"
            f"     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id\n"
            f"     WHERE s.email = '{email}' LIMIT 1)"
        )
        row_str = (
            f"  (\n"
            f"{ans_subquery},\n"
            f"    {row['idx_socioeconomic_digital']:.2f}, {row['idx_work_overload']:.2f}, "
            f"{row['idx_school_bonding']:.2f}, {row['idx_political_engagement']:.2f}, {row['idx_cultural_capital']:.2f},\n"
            f"    {int(row['cluster'])}, '{ped_profile}', {pca_1:.3f}, {pca_2:.3f}\n"
            f"  )"
        )
        value_rows.append(row_str)

    lines.append(",\n".join(value_rows))
    lines.append("ON CONFLICT (answer_id) DO UPDATE SET")
    lines.append("  idx_socioeconomic_digital = EXCLUDED.idx_socioeconomic_digital,")
    lines.append("  idx_work_overload = EXCLUDED.idx_work_overload,")
    lines.append("  idx_school_bonding = EXCLUDED.idx_school_bonding,")
    lines.append("  idx_political_engagement = EXCLUDED.idx_political_engagement,")
    lines.append("  idx_cultural_capital = EXCLUDED.idx_cultural_capital,")
    lines.append("  cluster_id = EXCLUDED.cluster_id,")
    lines.append("  pedagogical_profile = EXCLUDED.pedagogical_profile,")
    lines.append("  pca_1 = EXCLUDED.pca_1,")
    lines.append("  pca_2 = EXCLUDED.pca_2,")
    lines.append("  updated_at = NOW();\n")

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
        upsert_query = """
        INSERT INTO student_analytics (
            answer_id, idx_socioeconomic_digital, idx_work_overload, idx_school_bonding,
            idx_political_engagement, idx_cultural_capital, cluster_id, pedagogical_profile,
            pca_1, pca_2, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (answer_id) DO UPDATE SET
            idx_socioeconomic_digital = EXCLUDED.idx_socioeconomic_digital,
            idx_work_overload = EXCLUDED.idx_work_overload,
            idx_school_bonding = EXCLUDED.idx_school_bonding,
            idx_political_engagement = EXCLUDED.idx_political_engagement,
            idx_cultural_capital = EXCLUDED.idx_cultural_capital,
            cluster_id = EXCLUDED.cluster_id,
            pedagogical_profile = EXCLUDED.pedagogical_profile,
            pca_1 = EXCLUDED.pca_1,
            pca_2 = EXCLUDED.pca_2,
            updated_at = NOW();
        """
        saved = 0
        for _, row in df.iterrows():
            ans_id = row.get('answer_id')
            if pd.isna(ans_id) or ans_id is None:
                cur.execute("""
                    SELECT da.id FROM diagnosis_answer da
                    JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
                    WHERE s.email = %s LIMIT 1;
                """, (row.get('email'),))
                res = cur.fetchone()
                if res:
                    ans_id = res[0]
                else:
                    continue
            cur.execute(upsert_query, (
                int(ans_id), float(row['idx_socioeconomic_digital']), float(row['idx_work_overload']),
                float(row['idx_school_bonding']), float(row['idx_political_engagement']),
                float(row['idx_cultural_capital']), int(row['cluster']), str(row['pedagogical_profile']),
                float(row.get('pca_1', 0.0)), float(row.get('pca_2', 0.0))
            ))
            saved += 1
        conn.commit()
        cur.close()
        conn.close()
        print(f"Total de {saved} registros gravados em 'student_analytics' com sucesso!")
    except Exception as e:
        print(f"Erro ao gravar resultados analíticos no PostgreSQL: {e}")
