"""
gerar_dados_sinteticos.py
=========================
Gerador limpo e modular de dados sintéticos para o Diagnóstico Estudantil (TCC).
Gera dados realistas com Faker (pt_BR) e exporta diretamente para:
1. CSV ('dados_estudantes_simulados.csv') - Carregamento instantâneo pelo Pandas.
2. SQL ('postgresql/dados_revisada.sql') - Arquivo para execução no PostgreSQL.
3. Banco de Dados ('db') - Inserção direta via psycopg2.
"""

import os
import random
import unicodedata
import pandas as pd

try:
    from faker import Faker
    fake = Faker("pt_BR")
except ImportError:
    raise ImportError("Instale o Faker: pip install faker")

try:
    import psycopg2
except ImportError:
    psycopg2 = None


# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
SEED = 42
NUM_TURMAS = 3
ALUNOS_POR_TURMA = 5
GRADES = ["8º ano", "8º ano", "9º ano"]
CLASS_LABELS = ["A", "B", "A"]

MODO = "ambos"  # 'csv', 'sql', 'ambos' ou 'db'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "dados_estudantes_simulados.csv")
OUTPUT_SQL = os.path.join(PROJECT_ROOT, "postgresql", "dados_revisada.sql")

DB_CONFIG = {
    "host": "localhost",
    "database": "perfil_estudantil",
    "user": "seu_usuario",
    "password": "sua_senha",
    "port": 5432,
}
SCHEMA = "sc_student_diagnosis"

PROFESSOR_EMAIL = "maria.prof@escola.com"
PROFESSOR_NOME = "Maria da Silva Santos"
PROFESSOR_USER = "prof_maria"
ADMIN_EMAIL = "jose.admin@escola.com"
TITULO_DIAGNOSTICO = "Diagnóstico Inicial 2026 - 1º Bimestre"

RENDAS = [
    "Até 1 salário mínimo",
    "Entre 1 e 2 salários mínimos",
    "Entre 2 e 4 salários mínimos",
    "Entre 4 e 6 salários mínimos",
    "Acima de 6 salários mínimos",
]

ESCOLARIDADE_PAIS = [
    "Sem escolaridade",
    "Ensino fundamental incompleto",
    "Ensino fundamental completo",
    "Ensino médio incompleto",
    "Ensino médio completo",
    "Ensino superior incompleto",
    "Ensino superior completo",
    "Pós-graduação",
]

ATIVIDADES_CULTURAIS = [
    "Leitura, música e esportes",
    "Futebol e jogos digitais",
    "Teatro, dança e leitura",
    "Música e artes visuais",
    "Esportes coletivos e voluntariado",
    "Desenho, cinema e fotografia",
    "Capoeira e dança folclórica",
    "Jogos de tabuleiro e leitura",
    "Violão, canto e coral da igreja",
]

TRADICOES = [
    "Festa junina da comunidade",
    "Tradições de origem nordestina",
    "Grupos culturais da igreja local",
    "Feira do bairro e festas de rua",
    "Quadrilha e danças regionais",
    "Congada e manifestações afro-brasileiras",
    "Festas de aniversário comunitárias",
]

PAPEL_FAMILIA = [
    "Incentiva os estudos e a participação em eventos locais",
    "A família valoriza o trabalho e a cooperação",
    "Apoia a criatividade e a continuidade dos estudos",
    "Foca em disciplina e responsabilidade",
    "Estimula a leitura e o diálogo em casa",
    "Pouco envolvimento, mas apoia à distância",
    "Envolve a criança nas decisões da casa",
    "Prioriza a estabilidade financeira acima de tudo",
]

PAPEL_EDUCACAO = [
    "A educação ajuda a formar cidadãos críticos e conscientes",
    "A educação pode melhorar oportunidades e reduzir desigualdades",
    "A escola é fundamental para transformar a sociedade",
    "Educação é a principal ferramenta de ascensão social",
    "A escola deve preparar para o mercado de trabalho",
]

RELACAO_PROFESSORES = [
    "Boa e respeitosa",
    "Razoável, com alguns conflitos pontuais",
    "Muito boa e acolhedora",
    "Distante, mas sem grandes problemas",
    "Difícil, falta diálogo com alguns professores",
    "Excelente, me sinto apoiada",
    "Regular, depende muito do professor",
]

DIFICULDADES = [
    "Falta de tempo para estudar em casa",
    "Dificuldade em matemática e falta de materiais",
    "Metodologias muito rápidas em algumas disciplinas",
    "Conciliar trabalho e escola",
    "Falta de concentração e motivação",
    "Falta de apoio familiar nos estudos",
]

OBJETIVOS = [
    "Entrar na universidade e trabalhar com saúde",
    "Concluir os estudos e abrir um negócio próprio",
    "Seguir carreira na área de tecnologia",
    "Ser professor e contribuir com a educação",
    "Trabalhar com música e artes",
    "Fazer medicina e ajudar a comunidade",
]

APOIO_ESCOLA = [
    "Mais orientação vocacional e reforço escolar",
    "Cursos técnicos e apoio para conciliar estudo e trabalho",
    "Projetos, laboratório de informática e orientação profissional",
    "Psicólogo escolar e espaço de escuta",
    "Bibliotecas e materiais de qualidade",
    "Programas de mentoria com profissionais da área",
]


def clean_ascii(text):
    """Remove acentos e caracteres especiais para emails limpos."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().replace(' ', '').replace('.', '')


def gerar_dados():
    """Gera o dataset sintético em formato tabular (lista de dicionários)."""
    random.seed(SEED)
    Faker.seed(SEED)

    turmas = [
        {"grade": GRADES[i], "class": CLASS_LABELS[i], "diagnostico": f"{TITULO_DIAGNOSTICO} - {GRADES[i]} {CLASS_LABELS[i]}"}
        for i in range(NUM_TURMAS)
    ]

    emails_usados = set()
    alunos = []

    for turma in turmas:
        for _ in range(ALUNOS_POR_TURMA):
            first = fake.first_name()
            last1 = fake.last_name()
            last2 = fake.last_name()
            nome = f"{first} {last1} {last2}"

            first_clean = clean_ascii(first)
            last_clean = clean_ascii(last2)
            email_base = f"{first_clean}.{last_clean}@escola.com"
            email = email_base
            sufixo = 1
            while email in emails_usados:
                email = f"{first_clean}.{last_clean}{sufixo}@escola.com"
                sufixo += 1
            emails_usados.add(email)

            renda = random.choices(RENDAS, weights=[25, 30, 25, 12, 8])[0]
            trabalha = random.choices([True, False], weights=[20, 80])[0]
            horas_trabalho = random.choice([10, 15, 20, 25, 30, 40]) if trabalha else None

            alunos.append({
                "full_name": nome,
                "email": email,
                "user_name": email.split("@")[0].replace(".", "_"),
                "grade": turma["grade"],
                "school_class": turma["class"],
                "diagnostico": turma["diagnostico"],
                "family_income": renda,
                "works_besides_studying": trabalha,
                "work_hours": horas_trabalho,
                "parents_education": random.choice(ESCOLARIDADE_PAIS),
                "has_internet": random.choices([True, False], weights=[78, 22])[0],
                "has_computer": random.choices([True, False], weights=[60, 40])[0],
                "cultural_activities": random.choice(ATIVIDADES_CULTURAIS),
                "community_tradition": random.choice(TRADICOES),
                "family_role": random.choice(PAPEL_FAMILIA),
                "follows_politics": random.choices([True, False], weights=[45, 55])[0],
                "participated_in_social_movement": random.choices([True, False], weights=[15, 85])[0],
                "education_role": random.choice(PAPEL_EDUCACAO),
                "teachers_relations": random.choice(RELACAO_PROFESSORES),
                "opinion_is_heard": random.choices([True, False], weights=[55, 45])[0],
                "learning_difficulties": random.choice(DIFICULDADES),
                "personal_professional_goals": random.choice(OBJETIVOS),
                "school_support": random.choice(APOIO_ESCOLA),
            })

    return turmas, alunos


def exportar_csv(alunos, path=OUTPUT_CSV):
    """Exporta diretamente para CSV limpo."""
    df = pd.DataFrame(alunos)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  -> CSV exportado com sucesso: {path} ({len(df)} alunos)")


def exportar_sql(turmas, alunos, path=OUTPUT_SQL):
    """Exporta o script SQL limpo e estruturado para execução no PostgreSQL."""
    q_str = lambda s: "'" + str(s).replace("'", "''") + "'"
    q_bool = lambda b: "TRUE" if b else "FALSE"
    q_num = lambda n: "NULL" if n is None else str(n)

    lines = [
        "-- dados_revisada.sql",
        f"-- Dataset de Diagnóstico Estudantil: {len(alunos)} alunos em {len(turmas)} turmas.",
        f"SET search_path TO {SCHEMA}, public;\n",
        "-- 1) USUÁRIOS",
        "INSERT INTO users (name_user, email, password, function) VALUES",
        f"  ('admin_jose', '{ADMIN_EMAIL}', 'hash_admin', 'admin'),",
        f"  ('{PROFESSOR_USER}', '{PROFESSOR_EMAIL}', 'hash_prof', 'professor'),"
    ]

    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({q_str(a['user_name'])}, {q_str(a['email'])}, 'hash_aluno', 'aluno'){sep}")
    lines.append("ON CONFLICT (email) DO NOTHING;\n")

    lines += [
        "-- 2) PROFESSORA",
        "INSERT INTO teachers (user_id, full_name, email) VALUES",
        f"  ((SELECT id FROM users WHERE email = '{PROFESSOR_EMAIL}' LIMIT 1), '{PROFESSOR_NOME}', '{PROFESSOR_EMAIL}')",
        "ON CONFLICT (email) DO NOTHING;\n",
        "-- 3) ALUNOS",
        "INSERT INTO student (user_id, full_name, email, grade, class) VALUES"
    ]
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ((SELECT id FROM users WHERE email = {q_str(a['email'])} LIMIT 1), {q_str(a['full_name'])}, {q_str(a['email'])}, {q_str(a['grade'])}, {q_str(a['school_class'])}){sep}")
    lines.append("ON CONFLICT (email) DO NOTHING;\n")

    lines += [
        "-- 4) PEDIDOS DE DIAGNÓSTICO",
        "INSERT INTO diagnostic_requests (teacher_id, title, description, grade, class, status) VALUES"
    ]
    for i, t in enumerate(turmas):
        sep = "," if i < len(turmas) - 1 else ""
        lines.append(f"  ((SELECT id FROM teachers WHERE email = '{PROFESSOR_EMAIL}' LIMIT 1), {q_str(t['diagnostico'])}, 'Mapeamento diagnóstico', {q_str(t['grade'])}, {q_str(t['class'])}, 'aberto'){sep}")
    lines.append("ON CONFLICT DO NOTHING;\n")

    lines += [
        "-- 5) RESPOSTAS",
        "INSERT INTO diagnosis_answer (order_id, student_id) VALUES"
    ]
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ((SELECT id FROM diagnostic_requests WHERE title = {q_str(a['diagnostico'])} LIMIT 1), (SELECT id FROM student WHERE email = {q_str(a['email'])} LIMIT 1)){sep}")
    lines.append("ON CONFLICT (order_id, student_id) DO NOTHING;\n")

    ans_subquery = lambda a: f"(SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = {q_str(a['email'])} AND p.title = {q_str(a['diagnostico'])} LIMIT 1)"

    # 6) Dimensões
    lines.append("-- 6) DADOS SOCIOECONÔMICOS")
    lines.append("INSERT INTO socioeconomic_data (answer_id, family_income, works_besides_studying, work_hours_per_week, parents_education, has_internet_at_home, has_computer_at_home) VALUES")
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({ans_subquery(a)}, {q_str(a['family_income'])}, {q_bool(a['works_besides_studying'])}, {q_num(a['work_hours'])}, {q_str(a['parents_education'])}, {q_bool(a['has_internet'])}, {q_bool(a['has_computer'])}){sep}")
    lines.append("ON CONFLICT (answer_id) DO NOTHING;\n")

    lines.append("-- 7) CONTEXTO CULTURAL")
    lines.append("INSERT INTO cultural_context (answer_id, cultural_activities, community_cultural_tradition, role_family_community_training) VALUES")
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({ans_subquery(a)}, {q_str(a['cultural_activities'])}, {q_str(a['community_tradition'])}, {q_str(a['family_role'])}){sep}")
    lines.append("ON CONFLICT (answer_id) DO NOTHING;\n")

    lines.append("-- 8) DIMENSÃO POLÍTICA")
    lines.append("INSERT INTO political_dimension (answer_id, follows_politics_society_news, participated_in_social_movement, role_education_social_transformation) VALUES")
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({ans_subquery(a)}, {q_bool(a['follows_politics'])}, {q_bool(a['participated_in_social_movement'])}, {q_str(a['education_role'])}){sep}")
    lines.append("ON CONFLICT (answer_id) DO NOTHING;\n")

    lines.append("-- 9) EXPERIÊNCIAS ESCOLARES")
    lines.append("INSERT INTO school_experiences (answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties) VALUES")
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({ans_subquery(a)}, {q_str(a['teachers_relations'])}, {q_bool(a['opinion_is_heard'])}, {q_str(a['learning_difficulties'])}){sep}")
    lines.append("ON CONFLICT (answer_id) DO NOTHING;\n")

    lines.append("-- 10) EXPECTATIVAS E SONHOS")
    lines.append("INSERT INTO expectations_dreams (answer_id, personal_professional_goals, support_that_the_school_should_offer) VALUES")
    for i, a in enumerate(alunos):
        sep = "," if i < len(alunos) - 1 else ""
        lines.append(f"  ({ans_subquery(a)}, {q_str(a['personal_professional_goals'])}, {q_str(a['school_support'])}){sep}")
    lines.append("ON CONFLICT (answer_id) DO NOTHING;\n")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  -> SQL exportado com sucesso: {path} ({os.path.getsize(path)/1024:.1f} KB)")


if __name__ == "__main__":
    print(f"Gerando dados sintéticos ({NUM_TURMAS} turmas x {ALUNOS_POR_TURMA} alunos)...")
    turmas, alunos = gerar_dados()

    if MODO in ("csv", "ambos"):
        exportar_csv(alunos)
    if MODO in ("sql", "ambos"):
        exportar_sql(turmas, alunos)

    print("Concluído!")
