"""
Módulo Avançado de Análise de Perfil Estudantil (TCC)
Integração completa com as 5 dimensões do Questionário de Diagnóstico Estudantil:
1. Identificação Pessoal (full_name, email, grade, school_class)
2. Socioeconômico e Inclusão Digital (renda, trabalho, escolaridade, internet, computador)
3. Contexto Cultural (atividades culturais, tradições comunitárias, papel da família)
4. Dimensão Política e Cidadã (notícias, movimentos sociais, visão da educação)
5. Experiências Escolares (relação com professores, escuta ativa, dificuldades de aprendizagem)
6. Expectativas e Sonhos de Futuro (objetivos profissionais, apoio escolar demandado)

Aplica Engenharia de Índices Pedagógicos, PCA 2D, K-Means com Profiling Descritivo,
Nuvens de Palavras Temáticas Segmentadas e Exportação de Relatórios Completos.
"""

# Módulos do sistema para manipulação de caminhos de arquivos e expressões regulares
import os
import re

# Bibliotecas de manipulação e análise estatística de dados
import pandas as pd
import numpy as np

# Bibliotecas para geração de visualizações gráficas acadêmicas
import matplotlib.pyplot as plt
import seaborn as sns

# Modelos de aprendizado de máquina não supervisionado do scikit-learn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Importações condicionais para bibliotecas opcionais
try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


# ==============================================================================
# CONFIGURAÇÕES DE AMBIENTE E BANCO DE DADOS
# ==============================================================================

# Seletor de origem dos dados:
# False: Lê diretamente do arquivo SQL (dados_revisada.sql) usando o parser nativo (sem precisar de banco rodando)
# True: Executa uma consulta relacional JOIN em uma instância ativa do PostgreSQL
USE_POSTGRESQL_DB = False

# Credenciais de conexão com o banco PostgreSQL (usado quando USE_POSTGRESQL_DB for True)
DB_CONFIG = {
    "host": "localhost",
    "database": "perfil_estudantil",
    "user": "seu_usuario",
    "password": "sua_senha",
    "port": 5432
}


# ==============================================================================
# FUNÇÕES DE PARSER E EXTRAÇÃO DE DADOS DO ARQUIVO SQL
# ==============================================================================

def parse_sql_value(val_str):
    """Converte valores literais do SQL em tipos de dados nativos equivalentes do Python."""
    val_str = val_str.strip()
    if (val_str.startswith("'") and val_str.endswith("'")) or (val_str.startswith('"') and val_str.endswith('"')):
        return val_str[1:-1].replace("''", "'")
    if val_str.upper() == "TRUE":
        return True
    if val_str.upper() == "FALSE":
        return False
    if val_str.upper() == "NULL":
        return None
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


def split_sql_values(values_str):
    """Divide argumentos SQL separados por vírgula preservando vírgulas dentro de textos com aspas."""
    values = []
    current_chars = []
    in_quote = False
    quote_char = None
    for char in values_str:
        if char in ("'", '"'):
            if not in_quote:
                in_quote = True
                quote_char = char
            elif quote_char == char:
                in_quote = False
                quote_char = None
            current_chars.append(char)
        elif char == ',' and not in_quote:
            values.append("".join(current_chars).strip())
            current_chars = []
        else:
            current_chars.append(char)
    if current_chars:
        values.append("".join(current_chars).strip())
    return [parse_sql_value(v) for v in values]


def find_sql_file():
    """Localiza o arquivo de dados SQL (dados_revisada.sql ou variantes) nos diretórios do projeto."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "postgresql", "dados_revisada.sql"),
        os.path.join(script_dir, "..", "postgresql", "dados_revisados.sql"),
        os.path.join(script_dir, "dados_revisada.sql"),
        os.path.join(script_dir, "..", "postgresql", "dados.sql"),
        os.path.join(os.getcwd(), "postgresql", "dados_revisada.sql"),
        os.path.join(os.getcwd(), "dados_revisada.sql"),
    ]
    for path in candidates:
        norm_path = os.path.normpath(path)
        if os.path.isfile(norm_path):
            return norm_path
    raise FileNotFoundError(
        "Arquivo SQL de dados não encontrado. Foram verificados os seguintes caminhos:\n" +
        "\n".join(f" - {c}" for c in candidates)
    )


def load_data_from_sql_file(sql_file_path):
    """Analisa o script SQL e consolida todas as 5 dimensões do questionário dos alunos."""
    with open(sql_file_path, "r", encoding="utf-8") as file:
        content = file.read()

    students_data = {}

    # Padrão regex para capturar registros de alunos na tabela 'students' ou 'alunos'
    students_pattern = re.compile(
        r"\(\s*(?:\(SELECT\b[\s\S]*?email\s*=\s*'([^']+)'[\s\S]*?\)|NULL|\d+)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
        re.IGNORECASE
    )

    students_block = re.search(
        r"INSERT\s+INTO\s+(?:students|alunos)[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)", 
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

    # Padrão regex para extrair dimensões ligadas pelo e-mail do estudante na subconsulta
    dimension_pattern = re.compile(
        r"\(\s*\(SELECT\b[\s\S]*?a\.email\s*=\s*'([^']+)'[\s\S]*?\)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
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

    # Extração de cada tabela de dimensão (compatível com esquemas em inglês e português)
    process_table("socioeconomic_data", [
        "family_income", "works_besides_studying", "work_hours",
        "parents_education", "has_internet", "has_computer"
    ])
    process_table("dados_socioeconomicos", [
        "family_income", "works_besides_studying", "work_hours",
        "parents_education", "has_internet", "has_computer"
    ])

    process_table("cultural_context", [
        "cultural_activities", "community_tradition", "family_role"
    ])
    process_table("contexto_cultural", [
        "cultural_activities", "community_tradition", "family_role"
    ])

    process_table("political_dimension", [
        "follows_politics", "participated_in_social_movement", "education_role"
    ])
    process_table("dimensao_politica", [
        "follows_politics", "participated_in_social_movement", "education_role"
    ])

    process_table("school_experiences", [
        "teachers_relations", "opinion_is_heard", "learning_difficulties"
    ])
    process_table("experiencias_escolares", [
        "teachers_relations", "opinion_is_heard", "learning_difficulties"
    ])

    process_table("expectations_dreams", [
        "personal_professional_goals", "school_support"
    ])
    process_table("expectativas_sonhos", [
        "personal_professional_goals", "school_support"
    ])

    return pd.DataFrame(list(students_data.values()))


def load_data_from_database(config):
    """Obtém todas as dimensões dos alunos diretamente de uma instância ativa do PostgreSQL."""
    if psycopg2 is None:
        raise ImportError(
            "O módulo 'psycopg2' não está instalado. "
            "Instale com 'pip install psycopg2-binary' ou mantenha USE_POSTGRESQL_DB = False."
        )

    conn = psycopg2.connect(
        host=config["host"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        port=config.get("port", 5432)
    )

    query = """
    SELECT 
        s.full_name AS full_name,
        s.email,
        s.grade AS grade,
        s.class AS school_class,
        se.family_income AS family_income,
        se.works_besides_studying AS works_besides_studying,
        se.horas_trabalho_semana AS work_hours,
        se.parents_education AS parents_education,
        se.has_internet_at_home AS has_internet,
        se.has_computer_at_home AS has_computer,
        exp.opinion_is_heard_at_school AS opinion_is_heard,
        exp.teachers_relations AS teachers_relations,
        exp.learning_difficulties AS learning_difficulties,
        ed.personal_professional_goals AS personal_professional_goals,
        ed.support_that_the_school_should_offer AS school_support,
        cc.atividades_culturais AS cultural_activities,
        cc.community_cultural_tradition AS community_tradition,
        cc.role_family_community_training AS family_role,
        pol.follows_politics_society_news AS follows_politics,
        pol.participated_in_social_movement AS participated_in_social_movement,
        pol.role_education_social_transformation AS education_role
    FROM students s
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


# ==============================================================================
# ENGENHARIA DE RECURSOS: ÍNDICES PEDAGÓGICOS MULTIDIMENSIONAIS
# ==============================================================================

def calculate_pedagogical_indices(df):
    """
    Converte as respostas qualitativas e métricas quantitativas em indicadores
    sintéticos padronizados (escala de 0 a 10) para cada dimensão do questionário.
    """
    # 1. Harmonização de nomes de colunas (compatibilidade caso venha com nomes legados em português)
    column_aliases = {
        'nome_completo': 'full_name',
        'serie': 'grade',
        'turma': 'school_class',
        'renda_familiar': 'family_income',
        'horas_trabalho': 'work_hours',
        'trabalha_alem_de_estudar': 'works_besides_studying',
        'escolaridade_pais': 'parents_education',
        'acesso_internet': 'has_internet',
        'tem_computador': 'has_computer',
        'opiniao_ouvida': 'opinion_is_heard',
        'relacao_professores': 'teachers_relations',
        'dificuldades_aprendizado': 'learning_difficulties',
        'objetivos_pessoais_profissionais': 'personal_professional_goals',
        'apoio_escola': 'school_support',
        'atividades_culturais': 'cultural_activities',
        'acompanha_noticias': 'follows_politics'
    }
    for old_col, new_col in column_aliases.items():
        if old_col in df.columns and new_col not in df.columns:
            df[new_col] = df[old_col]

    # 2. Renda Familiar Estimada e Categorização
    income_num_map = {
        'até 2 salários mínimos': 2000.0,
        'entre 2 e 4 salários mínimos': 4500.0,
        'acima de 4 salários mínimos': 8000.0
    }
    income_cat_map = {
        'até 2 salários mínimos': 'Baixa (Até 2 SM)',
        'entre 2 e 4 salários mínimos': 'Média-baixa (2 a 4 SM)',
        'acima de 4 salários mínimos': 'Alta (> 4 SM)'
    }
    
    if 'family_income' not in df.columns:
        df['family_income'] = 'até 2 salários mínimos'

    if pd.api.types.is_numeric_dtype(df['family_income']):
        df['estimated_income'] = df['family_income'].fillna(2000.0)
        df['income_category'] = pd.cut(
            df['estimated_income'],
            bins=[0, 2000, 5000, 10000, 50000],
            labels=['Baixa', 'Média-baixa', 'Média-alta', 'Alta']
        )
    else:
        df['estimated_income'] = df['family_income'].map(income_num_map).fillna(2000.0)
        df['income_category'] = df['family_income'].map(income_cat_map).fillna('Baixa (Até 2 SM)')

    # 3. Escala Ordinal da Escolaridade dos Pais (1 a 4)
    education_map = {
        'Não alfabetizado': 1.0,
        'Ensino fundamental incompleto': 1.5,
        'Ensino fundamental completo': 2.0,
        'Ensino médio incompleto': 2.5,
        'Ensino médio completo': 3.0,
        'Ensino superior incompleto': 3.5,
        'Ensino superior completo': 4.0
    }
    if 'parents_education' not in df.columns:
        df['parents_education'] = 'Ensino fundamental completo'
    df['parents_education_score'] = df['parents_education'].map(education_map).fillna(2.5)

    # 4. Horas e Situação de Trabalho
    if 'work_hours' not in df.columns:
        df['work_hours'] = 0.0
    df['work_hours'] = pd.to_numeric(df['work_hours'], errors='coerce').fillna(0.0)

    if 'works_besides_studying' not in df.columns:
        df['works_besides_studying'] = 0
    df['works_besides_studying'] = df['works_besides_studying'].map(
        {True: 1, False: 0, 1: 1, 0: 0}
    ).fillna(0).astype(int)

    # 5. Inclusão Digital e Indicadores Binários
    binary_columns = ['has_internet', 'has_computer', 'opinion_is_heard', 'follows_politics', 'participated_in_social_movement']
    for col in binary_columns:
        if col in df.columns:
            df[col] = df[col].map({True: 1, False: 0, 1: 1, 0: 0}).fillna(0).astype(int)
        else:
            df[col] = 0

    # 6. Escala Ordinal da Relação com Professores (1 a 4)
    def map_teacher_relationship(text):
        if not isinstance(text, str):
            return 2.5
        text_lower = text.lower()
        if 'muito boa' in text_lower or 'excelente' in text_lower or 'acolhedora' in text_lower:
            return 4.0
        elif 'boa' in text_lower or 'respeitosa' in text_lower:
            return 3.0
        elif 'razoável' in text_lower or 'regular' in text_lower or 'conflito' in text_lower:
            return 2.0
        elif 'ruim' in text_lower or 'péssima' in text_lower or 'difícil' in text_lower:
            return 1.0
        return 2.5

    if 'teachers_relations' not in df.columns:
        df['teachers_relations'] = 'Boa e respeitosa'
    df['teachers_relations_score'] = df['teachers_relations'].apply(map_teacher_relationship)

    # 7. Quantificação de Capital Cultural Ativo (Diversidade de Práticas)
    def count_cultural_activities(text):
        if not isinstance(text, str) or not text.strip():
            return 1.0
        parts = [p.strip() for p in re.split(r'[,;/]|\be\b', text) if len(p.strip()) > 2]
        return min(len(parts), 5)

    if 'cultural_activities' not in df.columns:
        df['cultural_activities'] = ''
    df['cultural_activities_count'] = df['cultural_activities'].apply(count_cultural_activities)

    # --------------------------------------------------------------------------
    # CÁLCULO DOS ÍNDICES SINTÉTICOS NORMALIZADOS (Escala de 0 a 10)
    # --------------------------------------------------------------------------

    # A) Índice Socioeconômico e Digital (0 a 10)
    # Renda estimada (40%) + Escolaridade dos pais (30%) + Inclusão digital (30%)
    income_norm = ((df['estimated_income'] - 2000.0) / (8000.0 - 2000.0) * 10.0).clip(0.0, 10.0)
    education_norm = ((df['parents_education_score'] - 1.0) / 3.0 * 10.0).clip(0.0, 10.0)
    digital_norm = (((df['has_internet'] + df['has_computer']) / 2.0) * 10.0).clip(0.0, 10.0)
    df['idx_socioeconomic_digital'] = (income_norm * 0.4 + education_norm * 0.3 + digital_norm * 0.3).round(2)

    # B) Índice de Sobrecarga de Trabalho (0 a 10)
    # Pondera o peso da carga horária de trabalho sobre a rotina de estudos (40h semanais = 10)
    df['idx_work_overload'] = (df['work_hours'] / 40.0 * 10.0).clip(0.0, 10.0).round(2)

    # C) Índice de Clima e Vínculo Escolar (0 a 10)
    # Qualidade da relação com professores (70%) + Percepção de escuta ativa (30%)
    relationship_norm = ((df['teachers_relations_score'] - 1.0) / 3.0 * 10.0).clip(0.0, 10.0)
    listening_norm = (df['opinion_is_heard'] * 10.0).clip(0.0, 10.0)
    df['idx_school_bonding'] = (relationship_norm * 0.7 + listening_norm * 0.3).round(2)

    # D) Índice de Engajamento Cívico e Político (0 a 10)
    # Acompanha notícias (5 pts) + Participação em movimentos sociais/comunitários (5 pts)
    df['idx_political_engagement'] = (
        (df['follows_politics'] * 5.0 + df['participated_in_social_movement'] * 5.0)
    ).round(2)

    # E) Índice de Capital Cultural (0 a 10)
    # Baseado na quantidade e diversidade de práticas culturais declaradas
    df['idx_cultural_capital'] = ((df['cultural_activities_count'] / 4.0 * 10.0).clip(0.0, 10.0)).round(2)

    return df


# ==============================================================================
# CARACTERIZAÇÃO E PROFILING PEDAGÓGICO DOS CLUSTERS
# ==============================================================================

def characterize_clusters(df, index_columns):
    """
    Calcula as médias das dimensões por cluster e aplica regras heurísticas
    para nomear pedagogicamente cada grupo identificado pelo K-Means.
    """
    cluster_means = df.groupby('cluster')[index_columns].mean()
    profile_names = {}

    for c in cluster_means.index:
        vulnerability = 10.0 - cluster_means.loc[c, 'idx_socioeconomic_digital']
        work_burden = cluster_means.loc[c, 'idx_work_overload']
        politics = cluster_means.loc[c, 'idx_political_engagement']
        school_climate = cluster_means.loc[c, 'idx_school_bonding']
        culture = cluster_means.loc[c, 'idx_cultural_capital']

        if work_burden >= 4.0 or vulnerability >= 6.0:
            profile_names[c] = "Perfil Trabalhador / Vulnerabilidade Econômica"
        elif politics >= 6.0 and culture >= 6.0:
            profile_names[c] = "Perfil Engajado / Participativo e Cultural"
        elif school_climate >= 7.0 and cluster_means.loc[c, 'idx_socioeconomic_digital'] >= 6.0:
            profile_names[c] = "Perfil Conectado / Foco Tecnológico e Acadêmico"
        else:
            profile_names[c] = f"Perfil em Desenvolvimento (Grupo {c+1})"

    df['pedagogical_profile'] = df['cluster'].map(profile_names)
    return df, cluster_means, profile_names


# ==============================================================================
# GERAÇÃO DE NUVENS DE PALAVRAS TEMÁTICAS (NLP SEGMENTADO)
# ==============================================================================

def generate_thematic_wordclouds(df, script_dir):
    """
    Gera um painel com 3 nuvens de palavras temáticas independentes:
    1. Dificuldades de Aprendizagem
    2. Expectativas e Sonhos de Futuro
    3. Apoio Esperado da Escola
    """
    if WordCloud is None:
        print("Aviso: 'wordcloud' não está instalada. Execute 'pip install wordcloud' para gerar nuvens de palavras.")
        return

    portuguese_stopwords = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", 
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", 
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser", 
        "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", 
        "isso", "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus",
        "alguns", "alguma", "muito", "muitas", "muitos", "onde"
    }

    themes = [
        ("Dificuldades de Aprendizagem", "learning_difficulties", "Reds"),
        ("Expectativas e Sonhos de Futuro", "personal_professional_goals", "Purples"),
        ("Apoio Esperado da Escola", "school_support", "Blues")
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (title, column, palette) in enumerate(themes):
        ax = axes[idx]
        if column in df.columns:
            texts = df[column].dropna().astype(str).tolist()
            unified_text = " ".join(texts)
        else:
            unified_text = ""

        if unified_text.strip():
            wc = WordCloud(
                width=600,
                height=400,
                background_color="white",
                colormap=palette,
                stopwords=portuguese_stopwords,
                min_word_length=3
            ).generate(unified_text)

            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        else:
            ax.text(0.5, 0.5, "Sem dados textuais suficientes", ha="center", va="center")
            ax.set_title(title, fontsize=12, fontweight="bold")

        ax.axis("off")

    plt.suptitle("Nuvens de Palavras Segmentadas por Eixo do Diagnóstico", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()

    img_output_path = os.path.join(script_dir, "nuvens_palavras_segmentadas.png")
    plt.savefig(img_output_path, dpi=300, bbox_inches="tight")
    print(f"Nuvens de palavras salvas em: {img_output_path}")
    plt.show()


# ==============================================================================
# VISUALIZAÇÕES GRÁFICAS COMPARATIVAS (PCA, DIMENSÕES E TURMAS)
# ==============================================================================

def plot_comparative_charts(df, X_pca, pca, index_columns, cluster_means, profile_names, script_dir):
    """Plota o gráfico de dispersão PCA 2D e gráficos comparativos de dimensões por cluster e turma."""
    n_samples = len(df)
    n_components = X_pca.shape[1]

    # 1. Gráfico de Dispersão PCA 2D com Rótulo dos Alunos
    plt.figure(figsize=(9, 6))
    if n_components >= 2:
        sns.scatterplot(
            x=X_pca[:, 0],
            y=X_pca[:, 1],
            hue=df['pedagogical_profile'],
            palette='Set1',
            s=150,
            style=df['pedagogical_profile']
        )
        for i, name in enumerate(df['full_name']):
            plt.annotate(
                name,
                (X_pca[i, 0], X_pca[i, 1]),
                xytext=(8, 5),
                textcoords='offset points',
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
            )
        v1 = pca.explained_variance_ratio_[0] * 100
        v2 = pca.explained_variance_ratio_[1] * 100
        plt.xlabel(f"Componente Principal 1 ({v1:.1f}% da variância explicada)", fontsize=11)
        plt.ylabel(f"Componente Principal 2 ({v2:.1f}% da variância explicada)", fontsize=11)
    else:
        sns.scatterplot(x=X_pca[:, 0], y=[0] * n_samples, hue=df['pedagogical_profile'], s=150)
        plt.xlabel("Componente Principal 1")

    plt.title("Mapeamento de Perfis Estudantis (PCA 2D)", fontsize=13, fontweight='bold', pad=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    pca_output_path = os.path.join(script_dir, "grafico_clusters_pca.png")
    plt.savefig(pca_output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfico de PCA salvo em: {pca_output_path}")
    plt.show()

    # 2. Gráfico de Barras das 5 Dimensões Pedagógicas por Perfil de Cluster
    readable_index_names = {
        'idx_socioeconomic_digital': 'Socioeconômico / Digital',
        'idx_work_overload': 'Sobrecarga de Trabalho',
        'idx_school_bonding': 'Vínculo Escolar / Professores',
        'idx_political_engagement': 'Engajamento Cívico / Político',
        'idx_cultural_capital': 'Capital Cultural Ativo'
    }
    
    plot_means = cluster_means.rename(columns=readable_index_names)
    plot_means.index = [profile_names[c] for c in plot_means.index]

    plt.figure(figsize=(11, 5.5))
    plot_means.T.plot(kind='bar', figsize=(11, 5.5), colormap='viridis', edgecolor='black', width=0.75)
    plt.title("Comparativo das 5 Dimensões Pedagógicas por Perfil de Cluster (0 a 10)", fontsize=13, fontweight='bold', pad=12)
    plt.ylabel("Pontuação Média do Índice (0 a 10)", fontsize=11)
    plt.ylim(0, 10.5)
    plt.xticks(rotation=15, ha='right', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(title="Perfis Identificados", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

    dimension_output_path = os.path.join(script_dir, "grafico_dimensoes_clusters.png")
    plt.savefig(dimension_output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfico comparativo de dimensões salvo em: {dimension_output_path}")
    plt.show()

    # 3. Comparativo Agrupado por Série e Turma
    if 'grade' in df.columns and 'school_class' in df.columns:
        df['class_cohort'] = df['grade'] + " - Turma " + df['school_class']
        class_stats = df.groupby('class_cohort')[index_columns].mean().rename(columns=readable_index_names)
        
        plt.figure(figsize=(10, 5))
        class_stats.T.plot(kind='bar', figsize=(10, 5), colormap='coolwarm', edgecolor='black', width=0.6)
        plt.title("Médias das Dimensões Diagnósticas por Turma e Série", fontsize=12, fontweight='bold')
        plt.ylabel("Média (0 a 10)")
        plt.ylim(0, 10.5)
        plt.xticks(rotation=15, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.legend(title="Série / Turma", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()

        class_output_path = os.path.join(script_dir, "analise_por_turma.png")
        plt.savefig(class_output_path, dpi=300, bbox_inches='tight')
        print(f"Gráfico por turma salvo em: {class_output_path}")
        plt.show()


# ==============================================================================
# FLUXO PRINCIPAL DA APLICAÇÃO (PIPELINE)
# ==============================================================================

def main():
    """Função principal que orquestra a ingestão, transformação, clusterização e geração de relatórios."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Carregamento dos dados
    if USE_POSTGRESQL_DB:
        print("Conectando ao banco de dados PostgreSQL...")
        df = load_data_from_database(DB_CONFIG)
    else:
        sql_file_path = find_sql_file()
        print(f"Lendo dados diretamente do arquivo SQL:\n -> {sql_file_path}")
        df = load_data_from_sql_file(sql_file_path)

    if df.empty:
        raise ValueError("Nenhum registro foi encontrado na fonte de dados.")

    print(f"Total de estudantes carregados com sucesso: {len(df)}")

    # 2. Cálculo dos Índices Pedagógicos Multidimensionais
    df = calculate_pedagogical_indices(df)

    index_columns = [
        'idx_socioeconomic_digital',
        'idx_work_overload',
        'idx_school_bonding',
        'idx_political_engagement',
        'idx_cultural_capital'
    ]

    print("\n--- ÍNDICES MULTIDIMENSIONAIS DOS ESTUDANTES (0 a 10) ---")
    cols_to_print = ['full_name', 'grade', 'school_class'] + index_columns
    available_cols = [c for c in cols_to_print if c in df.columns]
    print(df[available_cols].to_string(index=False))

    # 3. Padronização da Matriz de Atributos
    X = df[index_columns]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Redução de Dimensionalidade com PCA 2D
    n_samples = len(df)
    n_features = X_scaled.shape[1]
    n_components = min(2, n_samples, n_features)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # 5. Clusterização com K-Means
    n_clusters = min(3, n_samples)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)

    # 6. Caracterização e Profiling Descritivo dos Grupos
    df, cluster_means, profile_names = characterize_clusters(df, index_columns)

    # 7. Geração de Gráficos e Visualizações
    plot_comparative_charts(
        df, X_pca, pca, index_columns, cluster_means, profile_names, script_dir
    )

    # 8. Nuvens de Palavras Temáticas Segmentadas
    generate_thematic_wordclouds(df, script_dir)

    # 9. Exportação do Relatório Consolidado em CSV
    csv_output_path = os.path.join(script_dir, "relatorio_perfil_estudantil_completo.csv")
    df.to_csv(csv_output_path, index=False, encoding='utf-8-sig')
    print(f"\nRelatório consolidado exportado para: {csv_output_path}")

    # 10. Resumo dos Perfis no Console
    print("\n" + "=" * 80)
    print("SÍNTESE DOS PERFIS ESTUDANTIS IDENTIFICADOS (TCC)")
    print("=" * 80)
    summary_columns = [
        'full_name', 'grade', 'school_class', 'income_category', 
        'work_hours', 'pedagogical_profile'
    ]
    available_summary_cols = [c for c in summary_columns if c in df.columns]
    final_summary = df[available_summary_cols]
    print(final_summary.to_string(index=False))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
