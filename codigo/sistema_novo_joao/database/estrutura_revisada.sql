-- estrutura_revisada.sql
-- Schema do Diagnóstico Estudantil adaptado para múltiplos pedidos e perfis (Aluno, Professor, Admin)
-- Baseado no modelo consolidado do TCC (sc_student_diagnosis)

-- 1) Configuração do Schema
CREATE SCHEMA IF NOT EXISTS sc_student_diagnosis;
SET search_path TO sc_student_diagnosis, public;

-- 2) Habilitar extensão para UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 3) Tabela de Escolas / Instituições de Ensino
CREATE TABLE IF NOT EXISTS schools (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    inep_code VARCHAR(20) UNIQUE,
    city VARCHAR(100),
    state VARCHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4) Tabela de Autenticação / Usuários 
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(100),
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255),
    function VARCHAR(50) NOT NULL CHECK (function IN ('aluno', 'professor', 'admin')),
    school_id BIGINT REFERENCES schools(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5) Tabela de Professores
CREATE TABLE IF NOT EXISTS teachers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(200) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    birth_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6) Vínculo Avançado: Professor em Múltiplas Escolas (N:N)
CREATE TABLE IF NOT EXISTS teacher_schools (
    teacher_id BIGINT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    PRIMARY KEY (teacher_id, school_id)
);

-- 7) Tabela de Alunos
CREATE TABLE IF NOT EXISTS student (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE RESTRICT,
    full_name VARCHAR(200) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    birth_date DATE,
    email VARCHAR(255) NOT NULL UNIQUE,
    grade VARCHAR(50) NOT NULL,
    class VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8) Pedidos de Diagnóstico (Criados pelos Professores)
CREATE TABLE IF NOT EXISTS diagnostic_requests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    grade VARCHAR(50) NOT NULL,
    class VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'encerrado')),
    opening_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closing_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9) Respostas do Diagnóstico (Cabeçalho de entrega da resposta do aluno)
CREATE TABLE IF NOT EXISTS diagnosis_answer (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES diagnostic_requests(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    send_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Garante que o aluno responde 1 vez por pedido, mas pode responder a novos pedidos futuros:
    CONSTRAINT unq_student_per_request UNIQUE (order_id, student_id)
);

-- 10) Dimensões do Questionário / Diagnóstico (Itens da Resposta)
CREATE TABLE IF NOT EXISTS socioeconomic_data (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    family_income VARCHAR(100),
    works_besides_studying BOOLEAN NOT NULL DEFAULT FALSE,
    work_hours_per_week INTEGER CHECK (work_hours_per_week >= 0 AND work_hours_per_week <= 168),
    parents_education VARCHAR(150),
    has_internet_at_home BOOLEAN,
    has_computer_at_home BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cultural_context (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    cultural_activities TEXT,
    community_cultural_tradition TEXT,
    role_family_community_training TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS political_dimension (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    follows_politics_society_news BOOLEAN,
    participated_in_social_movement BOOLEAN,
    role_education_social_transformation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS school_experiences (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    teachers_relations TEXT,
    opinion_is_heard_at_school BOOLEAN,
    learning_difficulties TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expectations_dreams (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    personal_professional_goals TEXT,
    support_that_the_school_should_offer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11) Índices de Busca e Performance
CREATE INDEX IF NOT EXISTS students_grade_class_idx ON student (grade, class);
CREATE INDEX IF NOT EXISTS orders_status_idx ON diagnostic_requests (status);
CREATE INDEX IF NOT EXISTS order_series_class_idx ON diagnostic_requests (grade, class);
CREATE INDEX IF NOT EXISTS student_answers_idx ON diagnosis_answer (student_id);
CREATE INDEX IF NOT EXISTS order_responses_idx ON diagnosis_answer (order_id);

-- 12) Tabela de Resultados Analíticos (Data Mart / Machine Learning)
-- Armazena os indicadores multidimensionais calculados, clusterização e projeção PCA gerados pela análise de dados
CREATE TABLE IF NOT EXISTS student_analytics (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    answer_id BIGINT NOT NULL UNIQUE REFERENCES diagnosis_answer(id) ON DELETE CASCADE,
    idx_socioeconomic_digital NUMERIC(4,2) NOT NULL,
    idx_work_overload NUMERIC(4,2) NOT NULL,
    idx_school_bonding NUMERIC(4,2) NOT NULL,
    idx_political_engagement NUMERIC(4,2) NOT NULL,
    idx_cultural_capital NUMERIC(4,2) NOT NULL,
    cluster_id INTEGER NOT NULL,
    pedagogical_profile VARCHAR(150) NOT NULL,
    pca_1 NUMERIC(6,3),
    pca_2 NUMERIC(6,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para buscas e relatórios analíticos
CREATE INDEX IF NOT EXISTS student_analytics_answer_idx ON student_analytics (answer_id);
CREATE INDEX IF NOT EXISTS student_analytics_cluster_idx ON student_analytics (cluster_id);

