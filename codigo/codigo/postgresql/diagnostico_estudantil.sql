-- 1) Criar o banco
-- CREATE DATABASE meu_teste;

-- 2) Conectar ao banco
-- \c meu_teste

SET search_path TO sc_diagnostico_estudantil, public;




-- 3) Criar tabelas
CREATE TABLE IF NOT EXISTS alunos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_completo VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    serie VARCHAR(50) NOT NULL,
    turma VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dados_socioeconomicos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL UNIQUE,
    renda_familiar VARCHAR(100),
    trabalha_alem_de_estudar BOOLEAN NOT NULL DEFAULT FALSE,
    horas_trabalho_semana INTEGER CHECK (horas_trabalho_semana >= 0),
    escolaridade_pais_responsaveis VARCHAR(150),
    tem_internet_casa BOOLEAN,
    tem_computador_casa BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_dados_socioeconomicos_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contexto_cultural (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL UNIQUE,
    atividades_culturais TEXT,
    tradicao_cultural_comunitaria TEXT,
    papel_familia_comunidade_formacao TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_contexto_cultural_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dimensao_politica (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL UNIQUE,
    acompanha_noticias_politica_sociedade BOOLEAN,
    participou_movimento_social BOOLEAN,
    papel_educacao_transformacao_social TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_dimensao_politica_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS experiencias_escolares (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL UNIQUE,
    relacao_professores TEXT,
    opiniao_e_ouvida_na_escola BOOLEAN,
    dificuldades_aprendizado TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_experiencias_escolares_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expectativas_sonhos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL UNIQUE,
    objetivos_pessoais_profissionais TEXT,
    apoio_que_a_escola_deveria_oferecer TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_expectativas_sonhos_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        ON DELETE CASCADE
);

-- 4) Criar índices
CREATE INDEX IF NOT EXISTS idx_alunos_serie ON alunos (serie);
CREATE INDEX IF NOT EXISTS idx_alunos_turma ON alunos (turma);
CREATE INDEX IF NOT EXISTS idx_dados_socioeconomicos_aluno ON dados_socioeconomicos (aluno_id);
CREATE INDEX IF NOT EXISTS idx_contexto_cultural_aluno ON contexto_cultural (aluno_id);
CREATE INDEX IF NOT EXISTS idx_dimensao_politica_aluno ON dimensao_politica (aluno_id);
CREATE INDEX IF NOT EXISTS idx_experiencias_escolares_aluno ON experiencias_escolares (aluno_id);
CREATE INDEX IF NOT EXISTS idx_expectativas_sonhos_aluno ON expectativas_sonhos (aluno_id);

-- 5) Inserir dados
INSERT INTO alunos (nome_completo, email, serie, turma)
VALUES
  ('Ana Clara Souza', 'ana.clara@example.com', '8º ano', 'A'),
  ('Bruno Henrique Lima', 'bruno.lima@example.com', '9º ano', 'B'),
  ('Carla Mendes Pereira', 'carla.pereira@example.com', '1º ano EM', 'C');

INSERT INTO dados_socioeconomicos (
  aluno_id, renda_familiar, trabalha_alem_de_estudar, horas_trabalho_semana,
  escolaridade_pais_responsaveis, tem_internet_casa, tem_computador_casa
)
VALUES
  (1, 'até 2 salários mínimos', FALSE, NULL, 'Ensino médio completo', TRUE, TRUE),
  (2, 'entre 2 e 4 salários mínimos', TRUE, 20, 'Ensino fundamental completo', TRUE, FALSE),
  (3, 'acima de 4 salários mínimos', FALSE, NULL, 'Ensino superior completo', TRUE, TRUE);

INSERT INTO contexto_cultural (
  aluno_id, atividades_culturais, tradicao_cultural_comunitaria, papel_familia_comunidade_formacao
)
VALUES
  (1, 'Leitura, música e esportes', 'Festa junina da comunidade', 'Incentiva os estudos e a participação em eventos locais'),
  (2, 'Futebol e música', 'Culturas de origem familiar nordestina', 'A família valoriza o trabalho e a cooperação'),
  (3, 'Teatro, leitura e dança', 'Participação em grupos culturais da igreja', 'Apoia a criatividade e a continuidade dos estudos');

INSERT INTO dimensao_politica (
  aluno_id, acompanha_noticias_politica_sociedade, participou_movimento_social,
  papel_educacao_transformacao_social
)
VALUES
  (1, TRUE, FALSE, 'A educação ajuda a formar cidadãos críticos e conscientes'),
  (2, FALSE, TRUE, 'A educação pode melhorar oportunidades e reduzir desigualdades'),
  (3, TRUE, TRUE, 'A escola é fundamental para transformar a sociedade por meio do conhecimento');

INSERT INTO experiencias_escolares (
  aluno_id, relacao_professores, opiniao_e_ouvida_na_escola, dificuldades_aprendizado
)
VALUES
  (1, 'Boa e respeitosa', TRUE, 'Falta de tempo para estudar em casa'),
  (2, 'Razoável, com alguns conflitos', FALSE, 'Dificuldade em matemática e falta de materiais'),
  (3, 'Muito boa e acolhedora', TRUE, 'Metodologias muito rápidas em algumas disciplinas');

INSERT INTO expectativas_sonhos (
  aluno_id, objetivos_pessoais_profissionais, apoio_que_a_escola_deveria_oferecer
)
VALUES
  (1, 'Entrar na universidade e trabalhar com saúde', 'Mais orientação vocacional e reforço escolar'),
  (2, 'Concluir os estudos e abrir um negócio próprio', 'Cursos técnicos e apoio para conciliar estudo e trabalho'),
  (3, 'Seguir carreira na área de tecnologia', 'Projetos, laboratório de informática e orientação profissional');
