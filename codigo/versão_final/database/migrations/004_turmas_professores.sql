-- 004_turmas_professores.sql
-- Registra as turmas lecionadas por cada professor.

SET search_path TO sc_student_diagnosis, public;

-- 1. Criar a tabela de associação entre professores e turmas.

CREATE TABLE IF NOT EXISTS teacher_classes (
    teacher_id BIGINT NOT NULL,
    school_id BIGINT NOT NULL,
    grade VARCHAR(50) NOT NULL,
    class VARCHAR(50) NOT NULL,

    CONSTRAINT pk_teacher_classes
        PRIMARY KEY (teacher_id, school_id, grade, class),

    CONSTRAINT fk_teacher_classes_school
        FOREIGN KEY (teacher_id, school_id)
        REFERENCES teacher_schools (teacher_id, school_id)
        ON DELETE CASCADE
);

-- 2. O vínculo inicial de turmas é inserido junto aos dados iniciais
-- (dados_revisada.sql), depois que professores e escolas já existem.
-- Assim a migração funciona tanto em bancos novos quanto existentes.