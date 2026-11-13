-- 005_remover_cpf_cidade_estado_nascimento_dimensao_politica.sql
-- Remove campos descontinuados do modelo de dados:
--   CPF, cidade, estado, data de nascimento e dimensão política.
-- A coluna full_name foi mantida conforme decisão de escopo.

ALTER TABLE users
    DROP COLUMN IF EXISTS cpf;

ALTER TABLE teachers
    DROP COLUMN IF EXISTS cpf,
    DROP COLUMN IF EXISTS birth_date;

ALTER TABLE student
    DROP COLUMN IF EXISTS cpf,
    DROP COLUMN IF EXISTS birth_date;

ALTER TABLE schools
    DROP COLUMN IF EXISTS city,
    DROP COLUMN IF EXISTS state;

DROP TABLE IF EXISTS political_dimension;

ALTER TABLE student_analytics
    DROP COLUMN IF EXISTS idx_political_engagement;
