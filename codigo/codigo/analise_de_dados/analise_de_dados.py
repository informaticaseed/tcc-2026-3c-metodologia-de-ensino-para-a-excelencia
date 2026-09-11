"""
Módulo Avançado de Análise de Perfil Estudantil (TCC)
Integração completa com as 5 dimensões do Diagnóstico Estudantil:
1. Dados Pessoais e Identificação (nome, e-mail, série, turma)
2. Dados Socioeconômicos e Inclusão Digital (renda, trabalho, escolaridade, internet, computador)
3. Contexto Cultural (atividades culturais, tradições, papel familiar)
4. Dimensão Política e Cidadã (notícias, movimentos sociais, visão da educação)
5. Experiências Escolares (professores, escuta ativa, dificuldades de aprendizagem)
6. Expectativas e Sonhos (metas de futuro, demandas de apoio à escola)

Aplica Engenharia de Índices Pedagógicos, PCA 2D, K-Means com Profiling Descritivo,
Nuvens de Palavras Temáticas Segmentadas e Exportação de Relatórios Completos.
"""

# Importa módulos do sistema para manipulação de arquivos, diretórios e expressões regulares
import os
import re

# Importa bibliotecas essenciais para análise de dados e estatística
import pandas as pd
import numpy as np

# Importa bibliotecas gráficas para visualizações acadêmicas
import matplotlib.pyplot as plt
import seaborn as sns

# Importa módulos de aprendizado de máquina não supervisionado do scikit-learn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Importações com fallback para bibliotecas opcionais
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
# False: Lê diretamente o arquivo SQL (dados_revisada.sql) via parser nativo (independente de servidor ativo)
# True: Executa consulta relacional JOIN em uma instância ativa do PostgreSQL
USAR_BANCO_POSTGRESQL = False

# Credenciais de acesso ao PostgreSQL (caso USAR_BANCO_POSTGRESQL seja ativado)
CONFIG_BANCO = {
    "host": "localhost",
    "database": "perfil_estudantil",
    "user": "seu_usuario",
    "password": "sua_senha",
    "port": 5432
}


# ==============================================================================
# PARSER E EXTRATOR TEXTUAL DO ARQUIVO SQL
# ==============================================================================

def parse_sql_value(v):
    """Converte literais do SQL para tipos de dados nativos do Python."""
    v = v.strip()
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        return v[1:-1].replace("''", "'")
    if v.upper() == "TRUE":
        return True
    if v.upper() == "FALSE":
        return False
    if v.upper() == "NULL":
        return None
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def split_sql_values(values_str):
    """Fatia a lista de argumentos SQL preservando vírgulas internas entre aspas."""
    values = []
    current = []
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
            current.append(char)
        elif char == ',' and not in_quote:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        values.append("".join(current).strip())
    return [parse_sql_value(v) for v in values]


def encontrar_arquivo_sql():
    """Localiza o arquivo dados_revisada.sql no diretório do projeto."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidatos = [
        os.path.join(script_dir, "..", "postgresql", "dados_revisada.sql"),
        os.path.join(script_dir, "..", "postgresql", "dados_revisados.sql"),
        os.path.join(script_dir, "dados_revisada.sql"),
        os.path.join(script_dir, "..", "postgresql", "dados.sql"),
        os.path.join(os.getcwd(), "postgresql", "dados_revisada.sql"),
        os.path.join(os.getcwd(), "dados_revisada.sql"),
    ]
    for caminho in candidatos:
        caminho_norm = os.path.normpath(caminho)
        if os.path.isfile(caminho_norm):
            return caminho_norm
    raise FileNotFoundError(
        "Arquivo SQL de dados não encontrado. Foram verificados:\n" +
        "\n".join(f" - {c}" for c in candidatos)
    )


def carregar_dados_do_arquivo_sql(caminho_sql):
    """Extrai do arquivo SQL os dados de alunos e consolida todas as 5 dimensões."""
    with open(caminho_sql, "r", encoding="utf-8") as f:
        conteudo = f.read()

    dados_alunos = {}

    # Expressão para capturar alunos na tabela students / alunos
    pattern_alunos = re.compile(
        r"\(\s*(?:\(SELECT\b[\s\S]*?email\s*=\s*'([^']+)'[\s\S]*?\)|NULL|\d+)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
        re.IGNORECASE
    )

    bloco_alunos = re.search(
        r"INSERT\s+INTO\s+(?:students|alunos)[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)", 
        conteudo, 
        re.IGNORECASE
    )
    if bloco_alunos:
        for match in pattern_alunos.finditer(bloco_alunos.group(1)):
            email_ref = match.group(1)
            resto = match.group(2)
            valores = split_sql_values(resto)
            if len(valores) >= 4:
                dados_alunos[valores[1] if valores[1] else email_ref] = {
                    "nome_completo": valores[0],
                    "email": valores[1] if valores[1] else email_ref,
                    "serie": valores[2],
                    "turma": valores[3]
                }

    # Expressão genérica para extrair qualquer dimensão associada pelo e-mail
    pattern_dimensao = re.compile(
        r"\(\s*\(SELECT\b[\s\S]*?a\.email\s*=\s*'([^']+)'[\s\S]*?\)\s*,\s*([\s\S]*?)\s*\)(?=\s*(?:,|;|\bON\s+CONFLICT\b|$))",
        re.IGNORECASE
    )

    def processar_tabela(nome_tabela, colunas):
        bloco = re.search(
            rf"INSERT\s+INTO\s+{nome_tabela}[\s\S]*?VALUES([\s\S]*?)(?:ON\s+CONFLICT|;)", 
            conteudo, 
            re.IGNORECASE
        )
        if not bloco:
            return
        for match in pattern_dimensao.finditer(bloco.group(1)):
            email = match.group(1)
            valores = split_sql_values(match.group(2))
            if email not in dados_alunos:
                dados_alunos[email] = {"email": email}
            for col, val in zip(colunas, valores):
                dados_alunos[email][col] = val

    # Extração de cada dimensão estruturada
    processar_tabela("socioeconomic_data", [
        "renda_familiar", "trabalha_alem_de_estudar", "horas_trabalho",
        "escolaridade_pais", "acesso_internet", "tem_computador"
    ])
    processar_tabela("dados_socioeconomicos", [
        "renda_familiar", "trabalha_alem_de_estudar", "horas_trabalho",
        "escolaridade_pais", "acesso_internet", "tem_computador"
    ])

    processar_tabela("cultural_context", [
        "atividades_culturais", "tradicao_cultural", "papel_familia"
    ])
    processar_tabela("contexto_cultural", [
        "atividades_culturais", "tradicao_cultural", "papel_familia"
    ])

    processar_tabela("political_dimension", [
        "acompanha_noticias", "participou_movimento_social", "papel_educacao"
    ])
    processar_tabela("dimensao_politica", [
        "acompanha_noticias", "participou_movimento_social", "papel_educacao"
    ])

    processar_tabela("school_experiences", [
        "relacao_professores", "opiniao_ouvida", "dificuldades_aprendizado"
    ])
    processar_tabela("experiencias_escolares", [
        "relacao_professores", "opiniao_ouvida", "dificuldades_aprendizado"
    ])

    processar_tabela("expectations_dreams", [
        "objetivos_pessoais_profissionais", "apoio_escola"
    ])
    processar_tabela("expectativas_sonhos", [
        "objetivos_pessoais_profissionais", "apoio_escola"
    ])

    return pd.DataFrame(list(dados_alunos.values()))


def carregar_dados_do_banco(config):
    """Consulta todas as dimensões consolidadas diretamente no banco PostgreSQL."""
    if psycopg2 is None:
        raise ImportError(
            "O módulo 'psycopg2' não está instalado. "
            "Instale-o com 'pip install psycopg2-binary' ou mantenha USAR_BANCO_POSTGRESQL = False."
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
        s.full_name AS nome_completo,
        s.email,
        s.grade AS serie,
        s.class AS turma,
        se.family_income AS renda_familiar,
        se.works_besides_studying AS trabalha_alem_de_estudar,
        se.horas_trabalho_semana AS horas_trabalho,
        se.parents_education AS escolaridade_pais,
        se.has_internet_at_home AS acesso_internet,
        se.has_computer_at_home AS tem_computador,
        exp.opinion_is_heard_at_school AS opiniao_ouvida,
        exp.teachers_relations AS relacao_professores,
        exp.learning_difficulties AS dificuldades_aprendizado,
        ed.personal_professional_goals AS objetivos_pessoais_profissionais,
        ed.support_that_the_school_should_offer AS apoio_escola,
        cc.atividades_culturais,
        cc.community_cultural_tradition AS tradicao_cultural,
        cc.role_family_community_training AS papel_familia,
        pol.follows_politics_society_news AS acompanha_noticias,
        pol.participated_in_social_movement AS participou_movimento_social,
        pol.role_education_social_transformation AS papel_educacao
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

def calcular_indices_pedagogicos(df):
    """
    Converte as respostas qualitativas e quantitativas em indicadores
    sintéticos padronizados de 0 a 10 para cada dimensão do questionário.
    """
    # 1. Renda Familiar Estimada e Categoria
    map_renda_num = {
        'até 2 salários mínimos': 2000.0,
        'entre 2 e 4 salários mínimos': 4500.0,
        'acima de 4 salários mínimos': 8000.0
    }
    map_renda_cat = {
        'até 2 salários mínimos': 'Baixa (Até 2 SM)',
        'entre 2 e 4 salários mínimos': 'Média-baixa (2 a 4 SM)',
        'acima de 4 salários mínimos': 'Alta (> 4 SM)'
    }
    if pd.api.types.is_numeric_dtype(df['renda_familiar']):
        df['renda_estimada'] = df['renda_familiar'].fillna(2000.0)
        df['categoria_renda'] = pd.cut(
            df['renda_estimada'],
            bins=[0, 2000, 5000, 10000, 50000],
            labels=['Baixa', 'Média-baixa', 'Média-alta', 'Alta']
        )
    else:
        df['renda_estimada'] = df['renda_familiar'].map(map_renda_num).fillna(2000.0)
        df['categoria_renda'] = df['renda_familiar'].map(map_renda_cat).fillna('Baixa (Até 2 SM)')

    # 2. Escala Ordinal da Escolaridade dos Pais (1 a 4)
    map_escolaridade = {
        'Não alfabetizado': 1.0,
        'Ensino fundamental incompleto': 1.5,
        'Ensino fundamental completo': 2.0,
        'Ensino médio incompleto': 2.5,
        'Ensino médio completo': 3.0,
        'Ensino superior incompleto': 3.5,
        'Ensino superior completo': 4.0
    }
    df['escolaridade_pais_score'] = df['escolaridade_pais'].map(map_escolaridade).fillna(2.5)

    # 3. Tratamento de Horas e Situação de Trabalho
    df['horas_trabalho'] = pd.to_numeric(df['horas_trabalho'], errors='coerce').fillna(0.0)
    df['trabalha_alem_de_estudar'] = df['trabalha_alem_de_estudar'].map(
        {True: 1, False: 0, 1: 1, 0: 0}
    ).fillna(0).astype(int)

    # 4. Inclusão Digital (Acesso a Internet e Computador)
    for col_bin in ['acesso_internet', 'tem_computador', 'opiniao_ouvida', 'acompanha_noticias', 'participou_movimento_social']:
        if col_bin in df.columns:
            df[col_bin] = df[col_bin].map({True: 1, False: 0, 1: 1, 0: 0}).fillna(0).astype(int)
        else:
            df[col_bin] = 0

    # 5. Escala Ordinal da Relação com Professores (1 a 4)
    def mapear_relacao_professores(txt):
        if not isinstance(txt, str):
            return 2.5
        txt_l = txt.lower()
        if 'muito boa' in txt_l or 'excelente' in txt_l or 'acolhedora' in txt_l:
            return 4.0
        elif 'boa' in txt_l or 'respeitosa' in txt_l:
            return 3.0
        elif 'razoável' in txt_l or 'regular' in txt_l or 'conflito' in txt_l:
            return 2.0
        elif 'ruim' in txt_l or 'péssima' in txt_l or 'difícil' in txt_l:
            return 1.0
        return 2.5

    df['relacao_professores_score'] = df['relacao_professores'].apply(mapear_relacao_professores)

    # 6. Quantificação de Capital Cultural Ativo (Diversidade de Práticas)
    def contar_atividades_culturais(txt):
        if not isinstance(txt, str) or not txt.strip():
            return 1.0
        # Divide por vírgula, 'e', barras ou ponto e vírgula
        partes = [p.strip() for p in re.split(r'[,;/]|\be\b', txt) if len(p.strip()) > 2]
        return min(len(partes), 5)

    df['qtd_atividades_culturais'] = df['atividades_culturais'].apply(contar_atividades_culturais)

    # --------------------------------------------------------------------------
    # CÁLCULO DOS ÍNDICES SINTÉTICOS NORMALIZADOS (0 a 10)
    # --------------------------------------------------------------------------

    # A) Índice Socioeconômico e Digital (0 a 10)
    # Renda (0-10) + Escolaridade Pais (0-10) + Inclusão Digital (0-10)
    renda_norm = (df['renda_estimada'] - 2000.0) / (8000.0 - 2000.0) * 10.0
    renda_norm = renda_norm.clip(0.0, 10.0)
    escolaridade_norm = (df['escolaridade_pais_score'] - 1.0) / 3.0 * 10.0
    digital_norm = ((df['acesso_internet'] + df['tem_computador']) / 2.0) * 10.0
    df['idx_socioeconomico_digital'] = (renda_norm * 0.4 + escolaridade_norm * 0.3 + digital_norm * 0.3).round(2)

    # B) Índice de Sobrecarga de Trabalho (0 a 10)
    # Reflete o impacto da carga de trabalho sobre a rotina escolar (40h semanais = 10)
    df['idx_sobrecarga_trabalho'] = (
        df['horas_trabalho'] / 40.0 * 10.0
    ).clip(0.0, 10.0).round(2)

    # C) Índice de Vínculo e Clima Escolar (0 a 10)
    # Combina relação com professores (70%) e sentimento de escuta ativa (30%)
    relacao_norm = (df['relacao_professores_score'] - 1.0) / 3.0 * 10.0
    escuta_norm = df['opiniao_ouvida'] * 10.0
    df['idx_vinculo_escolar'] = (relacao_norm * 0.7 + escuta_norm * 0.3).round(2)

    # D) Índice de Engajamento Cívico-Político (0 a 10)
    # Notícias (50%) + Participação em Movimentos (50%)
    df['idx_engajamento_politico'] = (
        (df['acompanha_noticias'] * 5.0 + df['participou_movimento_social'] * 5.0)
    ).round(2)

    # E) Índice de Capital Cultural (0 a 10)
    # Baseado na quantidade e diversidade de atividades culturais praticadas
    df['idx_capital_cultural'] = (
        (df['qtd_atividades_culturais'] / 4.0 * 10.0).clip(0.0, 10.0)
    ).round(2)

    return df


# ==============================================================================
# CARACTERIZAÇÃO E PROFILING PEDAGÓGICO DOS CLUSTERS
# ==============================================================================

def caracterizar_clusters(df, colunas_indices):
    """
    Gera diagnósticos descritivos com base nas médias dos índices
    para nomear pedagogicamente os grupos identificados pelo K-Means.
    """
    medias = df.groupby('cluster')[colunas_indices].mean()
    nomes_perfis = {}

    for c in medias.index:
        vulnerabilidade = 10.0 - medias.loc[c, 'idx_socioeconomico_digital']
        trabalho = medias.loc[c, 'idx_sobrecarga_trabalho']
        politica = medias.loc[c, 'idx_engajamento_politico']
        clima = medias.loc[c, 'idx_vinculo_escolar']
        cultura = medias.loc[c, 'idx_capital_cultural']

        # Regra heurística de caracterização sociopedagógica
        if trabalho >= 4.0 or vulnerabilidade >= 6.0:
            nomes_perfis[c] = "Perfil Trabalhador / Vulnerabilidade Econômica"
        elif politica >= 6.0 and cultura >= 6.0:
            nomes_perfis[c] = "Perfil Engajado / Participativo e Cultural"
        elif clima >= 7.0 and medias.loc[c, 'idx_socioeconomico_digital'] >= 6.0:
            nomes_perfis[c] = "Perfil Conectado / Foco Tecnológico e Acadêmico"
        else:
            nomes_perfis[c] = f"Perfil em Desenvolvimento (Grupo {c+1})"

    df['perfil_pedagogico'] = df['cluster'].map(nomes_perfis)
    return df, medias, nomes_perfis


# ==============================================================================
# GERAÇÃO DE NUVENS DE PALAVRAS TEMÁTICAS (NLP SEGMENTADO)
# ==============================================================================

def gerar_nuvens_tematicas(df, script_dir):
    """
    Gera um painel com 3 nuvens de palavras segmentadas por eixo do questionário:
    1. Dificuldades de Aprendizagem
    2. Expectativas e Sonhos de Futuro
    3. Apoio Esperado da Escola
    """
    if WordCloud is None:
        print("Aviso: 'wordcloud' não instalada. Instale com 'pip install wordcloud' para gerar nuvens.")
        return

    stopwords_pt = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", 
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", 
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser", 
        "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", 
        "isso", "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus",
        "alguns", "alguma", "muito", "muitas", "muitos", "onde"
    }

    temas = [
        ("Dificuldades de Aprendizagem", "dificuldades_aprendizado", "Reds"),
        ("Expectativas e Sonhos de Futuro", "objetivos_pessoais_profissionais", "Purples"),
        ("Apoio Esperado da Escola", "apoio_escola", "Blues")
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (titulo, coluna, paleta) in enumerate(temas):
        ax = axes[idx]
        if coluna in df.columns:
            textos = df[coluna].dropna().astype(str).tolist()
            texto_unificado = " ".join(textos)
        else:
            texto_unificado = ""

        if texto_unificado.strip():
            wc = WordCloud(
                width=600,
                height=400,
                background_color="white",
                colormap=paleta,
                stopwords=stopwords_pt,
                min_word_length=3
            ).generate(texto_unificado)

            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(titulo, fontsize=12, fontweight="bold", pad=10)
        else:
            ax.text(0.5, 0.5, "Sem dados textuais suficientes", ha="center", va="center")
            ax.set_title(titulo, fontsize=12, fontweight="bold")

        ax.axis("off")

    plt.suptitle("Nuvens de Palavras Segmentadas por Eixo do Diagnóstico", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()

    out_img = os.path.join(script_dir, "nuvens_palavras_segmentadas.png")
    plt.savefig(out_img, dpi=300, bbox_inches="tight")
    print(f"Nuvens de palavras segmentadas salvas em: {out_img}")
    plt.show()


# ==============================================================================
# VISUALIZAÇÕES COMPARATIVAS (PCA, ÍNDICES E TURMAS)
# ==============================================================================

def plotar_graficos_comparativos(df, X_pca, pca, colunas_indices, medias_clusters, nomes_perfis, script_dir):
    """Gera o gráfico de dispersão PCA e o gráfico comparativo das dimensões por cluster."""
    n_samples = len(df)
    n_components = X_pca.shape[1]

    # 1. Gráfico de Dispersão PCA 2D com Identificação Nominal
    plt.figure(figsize=(9, 6))
    if n_components >= 2:
        sns.scatterplot(
            x=X_pca[:, 0],
            y=X_pca[:, 1],
            hue=df['perfil_pedagogico'],
            palette='Set1',
            s=150,
            style=df['perfil_pedagogico']
        )
        for i, nome in enumerate(df['nome_completo']):
            plt.annotate(
                nome,
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
        sns.scatterplot(x=X_pca[:, 0], y=[0] * n_samples, hue=df['perfil_pedagogico'], s=150)
        plt.xlabel("Componente Principal 1")

    plt.title("Mapeamento de Perfis Estudantis (PCA 2D)", fontsize=13, fontweight='bold', pad=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    out_pca = os.path.join(script_dir, "grafico_clusters_pca.png")
    plt.savefig(out_pca, dpi=300, bbox_inches='tight')
    print(f"Gráfico de PCA salvo em: {out_pca}")
    plt.show()

    # 2. Gráfico de Barras Comparativo das 5 Dimensões por Perfil de Cluster
    nomes_legiveis_indices = {
        'idx_socioeconomico_digital': 'Socioeconômico / Digital',
        'idx_sobrecarga_trabalho': 'Sobrecarga de Trabalho',
        'idx_vinculo_escolar': 'Vínculo Escolar / Professores',
        'idx_engajamento_politico': 'Engajamento Cívico / Político',
        'idx_capital_cultural': 'Capital Cultural Ativo'
    }
    
    medias_plot = medias_clusters.rename(columns=nomes_legiveis_indices)
    medias_plot.index = [nomes_perfis[c] for c in medias_plot.index]

    plt.figure(figsize=(11, 5.5))
    medias_plot.T.plot(kind='bar', figsize=(11, 5.5), colormap='viridis', edgecolor='black', width=0.75)
    plt.title("Comparativo das 5 Dimensões Pedagógicas por Perfil de Cluster (0 a 10)", fontsize=13, fontweight='bold', pad=12)
    plt.ylabel("Pontuação Média do Índice (0 a 10)", fontsize=11)
    plt.ylim(0, 10.5)
    plt.xticks(rotation=15, ha='right', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(title="Perfis Identificados", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

    out_dim = os.path.join(script_dir, "grafico_dimensoes_clusters.png")
    plt.savefig(out_dim, dpi=300, bbox_inches='tight')
    print(f"Gráfico comparativo de dimensões salvo em: {out_dim}")
    plt.show()

    # 3. Análise Segmentada por Série e Turma (se houver dados suficientes)
    if 'serie' in df.columns and 'turma' in df.columns:
        df['turma_serie'] = df['serie'] + " - Turma " + df['turma']
        turma_stats = df.groupby('turma_serie')[colunas_indices].mean().rename(columns=nomes_legiveis_indices)
        
        plt.figure(figsize=(10, 5))
        turma_stats.T.plot(kind='bar', figsize=(10, 5), colormap='coolwarm', edgecolor='black', width=0.6)
        plt.title("Médias das Dimensões Diagnósticas por Turma e Série", fontsize=12, fontweight='bold')
        plt.ylabel("Média (0 a 10)")
        plt.ylim(0, 10.5)
        plt.xticks(rotation=15, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.legend(title="Série / Turma", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()

        out_turma = os.path.join(script_dir, "analise_por_turma.png")
        plt.savefig(out_turma, dpi=300, bbox_inches='tight')
        print(f"Gráfico por turma salvo em: {out_turma}")
        plt.show()


# ==============================================================================
# FLUXO PRINCIPAL DA APLICAÇÃO
# ==============================================================================

def main():
    """Função principal que orquestra todo o fluxo de análise e geração de relatórios."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Carregamento dos dados
    if USAR_BANCO_POSTGRESQL:
        print("Conectando ao banco de dados PostgreSQL...")
        df = carregar_dados_do_banco(CONFIG_BANCO)
    else:
        caminho_sql = encontrar_arquivo_sql()
        print(f"Lendo dados diretamente do arquivo SQL:\n -> {caminho_sql}")
        df = carregar_dados_do_arquivo_sql(caminho_sql)

    if df.empty:
        raise ValueError("Nenhum dado foi encontrado no arquivo SQL.")

    print(f"Alunos importados com sucesso: {len(df)}")

    # 2. Engenharia dos Índices Pedagógicos Multidimensionais
    df = calcular_indices_pedagogicos(df)

    colunas_indices = [
        'idx_socioeconomico_digital',
        'idx_sobrecarga_trabalho',
        'idx_vinculo_escolar',
        'idx_engajamento_politico',
        'idx_capital_cultural'
    ]

    print("\n--- ÍNDICES MULTIDIMENSIONAIS DOS ESTUDANTES (0 a 10) ---")
    cols_print = ['nome_completo', 'serie', 'turma'] + colunas_indices
    print(df[cols_print].to_string(index=False))

    # 3. Matriz de Atributos X e Padronização
    X = df[colunas_indices]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Redução de Dimensionalidade (PCA 2D)
    n_samples = len(df)
    n_features = X_scaled.shape[1]
    n_components = min(2, n_samples, n_features)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # 5. Agrupamento em Perfis com K-Means
    n_clusters = min(3, n_samples)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)

    # 6. Caracterização Descritiva dos Perfis
    df, medias_clusters, nomes_perfis = caracterizar_clusters(df, colunas_indices)

    # 7. Visualizações Gráficas
    plotar_graficos_comparativos(
        df, X_pca, pca, colunas_indices, medias_clusters, nomes_perfis, script_dir
    )

    # 8. Nuvens de Palavras Temáticas Segmentadas
    gerar_nuvens_tematicas(df, script_dir)

    # 9. Exportação do Relatório Consolidado em CSV
    out_csv = os.path.join(script_dir, "relatorio_perfil_estudantil_completo.csv")
    df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f"\nRelatório consolidado exportado para: {out_csv}")

    # 10. Resumo Geral de Perfis no Terminal
    print("\n" + "=" * 80)
    print("SÍNTESE DOS PERFIS ESTUDANTIS IDENTIFICADOS (TCC)")
    print("=" * 80)
    resumo_final = df[[
        'nome_completo', 'serie', 'turma', 'categoria_renda', 
        'horas_trabalho', 'perfil_pedagogico'
    ]]
    print(resumo_final.to_string(index=False))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
