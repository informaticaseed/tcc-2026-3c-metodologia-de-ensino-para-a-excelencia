
-- 003_integridade_respostas.sql
-- Garante que cada resposta corresponda à escola, série e turma
-- tanto do aluno quanto do pedido de diagnóstico.

SET search_path TO sc_student_diagnosis, public;

-- 1. Criar as chaves únicas compostas nas tabelas de origem.
-- Necessárias para que as chaves estrangeiras compostas funcionem.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_student_enrollment'
          AND conrelid = 'sc_student_diagnosis.student'::regclass
    ) THEN
        ALTER TABLE student
            ADD CONSTRAINT uq_student_enrollment
            UNIQUE (id, school_id, grade, class);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_request_target'
          AND conrelid = 'sc_student_diagnosis.diagnostic_requests'::regclass
    ) THEN
        ALTER TABLE diagnostic_requests
            ADD CONSTRAINT uq_request_target
            UNIQUE (id, school_id, grade, class);
    END IF;
END;
$$;

-- 2. Adicionar as novas colunas à tabela existente.

ALTER TABLE diagnosis_answer
    ADD COLUMN IF NOT EXISTS school_id BIGINT;

ALTER TABLE diagnosis_answer
    ADD COLUMN IF NOT EXISTS grade VARCHAR(50);

ALTER TABLE diagnosis_answer
    ADD COLUMN IF NOT EXISTS class VARCHAR(50);

-- 3. Preencher os dados das respostas já cadastradas
-- utilizando as informações dos respectivos alunos.

UPDATE diagnosis_answer AS da
SET
    school_id = st.school_id,
    grade = st.grade,
    class = st.class
FROM student AS st
WHERE st.id = da.student_id;

-- 4. Tornar as novas colunas obrigatórias.

ALTER TABLE diagnosis_answer
    ALTER COLUMN school_id SET NOT NULL;

ALTER TABLE diagnosis_answer
    ALTER COLUMN grade SET NOT NULL;

ALTER TABLE diagnosis_answer
    ALTER COLUMN class SET NOT NULL;

-- 5. Remover as antigas chaves estrangeiras individuais.
-- As novas chaves compostas passarão a proteger esses relacionamentos.

ALTER TABLE diagnosis_answer
    DROP CONSTRAINT IF EXISTS diagnosis_answer_order_id_fkey;

ALTER TABLE diagnosis_answer
    DROP CONSTRAINT IF EXISTS diagnosis_answer_student_id_fkey;

-- 6. Criar as chaves estrangeiras compostas.

ALTER TABLE diagnosis_answer
    DROP CONSTRAINT IF EXISTS fk_answer_student_target;

ALTER TABLE diagnosis_answer
    ADD CONSTRAINT fk_answer_student_target
    FOREIGN KEY (student_id, school_id, grade, class)
    REFERENCES student (id, school_id, grade, class)
    ON DELETE CASCADE;

ALTER TABLE diagnosis_answer
    DROP CONSTRAINT IF EXISTS fk_answer_request_target;

ALTER TABLE diagnosis_answer
    ADD CONSTRAINT fk_answer_request_target
    FOREIGN KEY (order_id, school_id, grade, class)
    REFERENCES diagnostic_requests (id, school_id, grade, class)
    ON DELETE CASCADE;

-- 7. Criar a função de preenchimento automático.

CREATE OR REPLACE FUNCTION preencher_dados_aluno_resposta()
RETURNS TRIGGER AS $$
BEGIN
    SELECT school_id, grade, class
    INTO NEW.school_id, NEW.grade, NEW.class
    FROM student
    WHERE id = NEW.student_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Aluno não encontrado.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Criar o gatilho.

DROP TRIGGER IF EXISTS trg_preencher_dados_aluno_resposta
ON diagnosis_answer;

CREATE TRIGGER trg_preencher_dados_aluno_resposta
BEFORE INSERT OR UPDATE OF student_id
ON diagnosis_answer
FOR EACH ROW
EXECUTE FUNCTION preencher_dados_aluno_resposta();
