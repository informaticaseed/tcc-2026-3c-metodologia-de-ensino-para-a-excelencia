-- 006_inep_obrigatorio.sql
-- Torna o código INEP obrigatório no cadastro de instituições de ensino.
--
-- A validação também é feita na aplicação (auth.create_school). A constraint
-- abaixo usa NOT VALID para não bloquear a migração caso existam registros
-- antigos sem INEP; novos registros e atualizações passam a ser validados.

ALTER TABLE schools
    ADD CONSTRAINT schools_inep_code_obrigatorio
    CHECK (inep_code IS NOT NULL) NOT VALID;
