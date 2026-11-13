-- 002_integridade_relacionamentos.sql
-- Garante que o professor esteja vinculado à escola
-- em que criou o pedido de diagnóstico.

ALTER TABLE sc_student_diagnosis.diagnostic_requests
    DROP CONSTRAINT IF EXISTS diagnostic_requests_teacher_id_fkey;

ALTER TABLE sc_student_diagnosis.diagnostic_requests
    DROP CONSTRAINT IF EXISTS diagnostic_requests_school_id_fkey;

ALTER TABLE sc_student_diagnosis.diagnostic_requests
    DROP CONSTRAINT IF EXISTS fk_request_teacher_school;

ALTER TABLE sc_student_diagnosis.diagnostic_requests
    ADD CONSTRAINT fk_request_teacher_school
    FOREIGN KEY (teacher_id, school_id)
    REFERENCES sc_student_diagnosis.teacher_schools
        (teacher_id, school_id)
    ON DELETE RESTRICT;