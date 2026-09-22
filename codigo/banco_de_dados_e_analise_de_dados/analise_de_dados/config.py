"""
config.py
=========
Configurações centralizadas, parâmetros de banco de dados, caminhos de arquivos
e dicionários de mapeamento para o módulo de Diagnóstico Estudantil.
"""

import os

# Diretórios base
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
POSTGRESQL_DIR = os.path.join(PROJECT_ROOT, "postgresql")

# Configuração de persistência e banco de dados
USE_POSTGRESQL_DB = False

DB_CONFIG = {
    "host": "localhost",
    "database": "perfil_estudantil",
    "user": "seu_usuario",
    "password": "sua_senha",
    "port": 5432
}

SCHEMA = "sc_student_diagnosis"

# Caminhos de arquivos de entrada e saída
DEFAULT_SIMULATED_CSV = os.path.join(PROJECT_ROOT, "dados_estudantes_simulados.csv")
CSV_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "relatorio_perfil_estudantil_completo.csv")
SQL_ANALYTICS_PATH = os.path.join(POSTGRESQL_DIR, "inserts_student_analytics.sql")

# Colunas dos 5 índices multidimensionais (0 a 10)
INDEX_COLUMNS = [
    'idx_socioeconomic_digital',
    'idx_work_overload',
    'idx_school_bonding',
    'idx_political_engagement',
    'idx_cultural_capital'
]

# Nomes legíveis para gráficos e relatórios
READABLE_INDEX_NAMES = {
    'idx_socioeconomic_digital': 'Socioeconômico / Digital',
    'idx_work_overload': 'Sobrecarga de Trabalho',
    'idx_school_bonding': 'Vínculo Escolar / Professores',
    'idx_political_engagement': 'Engajamento Cívico / Político',
    'idx_cultural_capital': 'Capital Cultural Ativo'
}

# Mapeamentos de faixas de renda familiar (suporta faixas sintéticas e legadas)
INCOME_NUM_MAP = {
    'até 1 salário mínimo': 1400.0,
    'ate 1 salario minimo': 1400.0,
    'até 2 salários mínimos': 2000.0,
    'ate 2 salarios minimos': 2000.0,
    'entre 1 e 2 salários mínimos': 2500.0,
    'entre 1 e 2 salarios minimos': 2500.0,
    'entre 2 e 4 salários mínimos': 4500.0,
    'entre 2 e 4 salarios minimos': 4500.0,
    'entre 4 e 6 salários mínimos': 7000.0,
    'entre 4 e 6 salarios minimos': 7000.0,
    'acima de 4 salários mínimos': 8000.0,
    'acima de 4 salarios minimos': 8000.0,
    'acima de 6 salários mínimos': 10000.0,
    'acima de 6 salarios minimos': 10000.0,
}

INCOME_CAT_MAP = {
    'até 1 salário mínimo': 'Baixa (Até 1 SM)',
    'ate 1 salario minimo': 'Baixa (Até 1 SM)',
    'até 2 salários mínimos': 'Baixa (Até 2 SM)',
    'ate 2 salarios minimos': 'Baixa (Até 2 SM)',
    'entre 1 e 2 salários mínimos': 'Baixa (1 a 2 SM)',
    'entre 1 e 2 salarios minimos': 'Baixa (1 a 2 SM)',
    'entre 2 e 4 salários mínimos': 'Média-baixa (2 a 4 SM)',
    'entre 2 e 4 salarios minimos': 'Média-baixa (2 a 4 SM)',
    'entre 4 e 6 salários mínimos': 'Média-alta (4 a 6 SM)',
    'entre 4 e 6 salarios minimos': 'Média-alta (4 a 6 SM)',
    'acima de 4 salários mínimos': 'Alta (> 4 SM)',
    'acima de 4 salarios minimos': 'Alta (> 4 SM)',
    'acima de 6 salários mínimos': 'Alta (> 6 SM)',
    'acima de 6 salarios minimos': 'Alta (> 6 SM)',
}

# Mapeamento ordinal de escolaridade dos responsáveis (1.0 a 4.5)
EDUCATION_MAP = {
    'não alfabetizado': 1.0,
    'nao alfabetizado': 1.0,
    'sem escolaridade': 1.0,
    'ensino fundamental incompleto': 1.5,
    'ensino fundamental completo': 2.0,
    'ensino médio incompleto': 2.5,
    'ensino medio incompleto': 2.5,
    'ensino médio completo': 3.0,
    'ensino medio completo': 3.0,
    'ensino superior incompleto': 3.5,
    'ensino superior completo': 4.0,
    'pós-graduação': 4.5,
    'pos-graduacao': 4.5,
    'pos graduacao': 4.5
}

