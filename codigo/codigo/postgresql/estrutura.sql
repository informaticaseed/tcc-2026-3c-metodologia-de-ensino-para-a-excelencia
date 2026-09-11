-- estrutura.sql
-- Schema do Diagnóstico Estudantil adaptado para múltiplos pedidos e perfis (Aluno, Professor, Admin)

-- 1) Configuração do Schema
CREATE SCHEMA IF NOT EXISTS sc_diagnostico_estudantil;
SET search_path TO sc_diagnostico_estudantil, public;

-- 2) Habilitar extensão para UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 3) Tabela de Autenticação / Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome_usuario VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    papel VARCHAR(50) NOT NULL CHECK (papel IN ('aluno', 'professor', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4) Tabela de Professores
CREATE TABLE IF NOT EXISTS professores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id UUID UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nome_completo VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5) Tabela de Alunos
CREATE TABLE IF NOT EXISTS alunos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id UUID UNIQUE REFERENCES usuarios(id) ON DELETE SET NULL,
    nome_completo VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    serie VARCHAR(50) NOT NULL,
    turma VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6) Pedidos de Diagnóstico (Criados pelos Professores)
CREATE TABLE IF NOT EXISTS pedidos_diagnostico (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    professor_id BIGINT NOT NULL REFERENCES professores(id) ON DELETE CASCADE,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    serie VARCHAR(50) NOT NULL,
    turma VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'encerrado')),
    data_abertura TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_encerramento TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7) Respostas do Diagnóstico (Cabeçalho de entrega da resposta do aluno)
CREATE TABLE IF NOT EXISTS respostas_diagnostico (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pedido_id BIGINT NOT NULL REFERENCES pedidos_diagnostico(id) ON DELETE CASCADE,
    aluno_id BIGINT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    data_envio TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Garante que o aluno responde 1 vez por pedido, mas pode responder a novos pedidos futuros:
    CONSTRAINT unq_aluno_por_pedido UNIQUE (pedido_id, aluno_id)
);

-- 8) Dimensões do Questionário / Diagnóstico (Itens da Resposta)
CREATE TABLE IF NOT EXISTS dados_socioeconomicos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resposta_id BIGINT NOT NULL UNIQUE REFERENCES respostas_diagnostico(id) ON DELETE CASCADE,
    renda_familiar VARCHAR(100),
    trabalha_alem_de_estudar BOOLEAN NOT NULL DEFAULT FALSE,
    horas_trabalho_semana INTEGER CHECK (horas_trabalho_semana >= 0 AND horas_trabalho_semana <= 168),
    escolaridade_pais_responsaveis VARCHAR(150),
    tem_internet_casa BOOLEAN,
    tem_computador_casa BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contexto_cultural (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resposta_id BIGINT NOT NULL UNIQUE REFERENCES respostas_diagnostico(id) ON DELETE CASCADE,
    atividades_culturais TEXT,
    tradicao_cultural_comunitaria TEXT,
    papel_familia_comunidade_formacao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dimensao_politica (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resposta_id BIGINT NOT NULL UNIQUE REFERENCES respostas_diagnostico(id) ON DELETE CASCADE,
    acompanha_noticias_politica_sociedade BOOLEAN,
    participou_movimento_social BOOLEAN,
    papel_educacao_transformacao_social TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS experiencias_escolares (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resposta_id BIGINT NOT NULL UNIQUE REFERENCES respostas_diagnostico(id) ON DELETE CASCADE,
    relacao_professores TEXT,
    opiniao_e_ouvida_na_escola BOOLEAN,
    dificuldades_aprendizado TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expectativas_sonhos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resposta_id BIGINT NOT NULL UNIQUE REFERENCES respostas_diagnostico(id) ON DELETE CASCADE,
    objetivos_pessoais_profissionais TEXT,
    apoio_que_a_escola_deveria_oferecer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9) Índices de Busca e Performance
CREATE INDEX IF NOT EXISTS idx_alunos_serie_turma ON alunos (serie, turma);
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos_diagnostico (status);
CREATE INDEX IF NOT EXISTS idx_pedidos_serie_turma ON pedidos_diagnostico (serie, turma);
CREATE INDEX IF NOT EXISTS idx_respostas_aluno ON respostas_diagnostico (aluno_id);
CREATE INDEX IF NOT EXISTS idx_respostas_pedido ON respostas_diagnostico (pedido_id);