"""
indices.py
==========
Engenharia de recursos pedagógicos e cálculo dos 5 índices multidimensionais (0 a 10).
"""

import re
import pandas as pd

try:
    from .config import INCOME_NUM_MAP, INCOME_CAT_MAP, EDUCATION_MAP
except (ImportError, ValueError):
    from config import INCOME_NUM_MAP, INCOME_CAT_MAP, EDUCATION_MAP


def map_teacher_relationship(text):
    """Converte o relato qualitativo sobre professores em escala ordinal de 1.0 a 4.0."""
    if not isinstance(text, str):
        return 2.5
    text_lower = text.lower()
    if 'muito boa' in text_lower or 'excelente' in text_lower or 'acolhedora' in text_lower:
        return 4.0
    elif 'boa' in text_lower or 'respeitosa' in text_lower:
        return 3.0
    elif 'razoável' in text_lower or 'razoavel' in text_lower or 'regular' in text_lower or 'conflito' in text_lower:
        return 2.0
    elif 'ruim' in text_lower or 'péssima' in text_lower or 'pessima' in text_lower or 'difícil' in text_lower or 'dificil' in text_lower:
        return 1.0
    return 2.5


def count_cultural_activities(text):
    """Conta a diversidade de práticas culturais ativas informadas pelo aluno."""
    if not isinstance(text, str) or not text.strip():
        return 1.0
    parts = [p.strip() for p in re.split(r'[,;/]|\be\b', text) if len(p.strip()) > 2]
    return min(len(parts), 5)


def calculate_pedagogical_indices(df):
    """
    Converte as respostas do questionário em indicadores sintéticos (escala 0 a 10).
    """
    df = df.copy()

    # 1. Harmonização de nomes de colunas
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

    # 2. Renda Familiar Estimada e Categoria
    if 'family_income' not in df.columns:
        df['family_income'] = 'entre 2 e 4 salários mínimos'

    if pd.api.types.is_numeric_dtype(df['family_income']):
        df['estimated_income'] = df['family_income'].fillna(4500.0)
        df['income_category'] = pd.cut(
            df['estimated_income'],
            bins=[0, 2000, 5000, 10000, 50000],
            labels=['Baixa', 'Média-baixa', 'Média-alta', 'Alta']
        )
    else:
        norm_income = df['family_income'].astype(str).str.strip().str.lower()
        df['estimated_income'] = norm_income.map(INCOME_NUM_MAP).fillna(4500.0)
        df['income_category'] = norm_income.map(INCOME_CAT_MAP).fillna('Média-baixa (2 a 4 SM)')

    # 3. Escala de Escolaridade dos Pais
    if 'parents_education' not in df.columns:
        df['parents_education'] = 'Ensino fundamental completo'
    norm_edu = df['parents_education'].astype(str).str.strip().str.lower()
    df['parents_education_score'] = norm_edu.map(EDUCATION_MAP).fillna(2.5)

    # 4. Trabalho e Horas
    if 'work_hours' not in df.columns:
        df['work_hours'] = 0.0
    df['work_hours'] = pd.to_numeric(df['work_hours'], errors='coerce').fillna(0.0)

    bool_map = {
        True: 1, False: 0, 1: 1, 0: 0, 1.0: 1, 0.0: 0,
        'True': 1, 'False': 0, 'true': 1, 'false': 0, 'TRUE': 1, 'FALSE': 0, 't': 1, 'f': 0
    }
    if 'works_besides_studying' not in df.columns:
        df['works_besides_studying'] = 0
    df['works_besides_studying'] = df['works_besides_studying'].map(bool_map).fillna(0).astype(int)

    # 5. Indicadores Binários
    binary_cols = ['has_internet', 'has_computer', 'opinion_is_heard', 'follows_politics', 'participated_in_social_movement']
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].map(bool_map).fillna(0).astype(int)
        else:
            df[col] = 0

    # 6. Relação com Professores e Práticas Culturais
    if 'teachers_relations' not in df.columns:
        df['teachers_relations'] = 'Boa e respeitosa'
    df['teachers_relations_score'] = df['teachers_relations'].apply(map_teacher_relationship)

    if 'cultural_activities' not in df.columns:
        df['cultural_activities'] = ''
    df['cultural_activities_count'] = df['cultural_activities'].apply(count_cultural_activities)

    # 7. Cálculo dos Índices Normalizados (0 a 10)
    income_norm = ((df['estimated_income'] - 1400.0) / (10000.0 - 1400.0) * 10.0).clip(0.0, 10.0)
    education_norm = ((df['parents_education_score'] - 1.0) / 3.5 * 10.0).clip(0.0, 10.0)
    digital_norm = (((df['has_internet'] + df['has_computer']) / 2.0) * 10.0).clip(0.0, 10.0)
    df['idx_socioeconomic_digital'] = (income_norm * 0.4 + education_norm * 0.3 + digital_norm * 0.3).round(2)

    df['idx_work_overload'] = (df['work_hours'] / 40.0 * 10.0).clip(0.0, 10.0).round(2)

    relationship_norm = ((df['teachers_relations_score'] - 1.0) / 3.0 * 10.0).clip(0.0, 10.0)
    listening_norm = (df['opinion_is_heard'] * 10.0).clip(0.0, 10.0)
    df['idx_school_bonding'] = (relationship_norm * 0.7 + listening_norm * 0.3).round(2)

    df['idx_political_engagement'] = ((df['follows_politics'] * 5.0 + df['participated_in_social_movement'] * 5.0)).round(2)
    df['idx_cultural_capital'] = ((df['cultural_activities_count'] / 4.0 * 10.0).clip(0.0, 10.0)).round(2)

    return df

