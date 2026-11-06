-- Migração: perfis administrativos
-- Versão: 001
-- Objetivo: configurar superadministrador e administrador institucional.

-- 1. Remover temporariamente as restrições anteriores.
ALTER TABLE sc_student_diagnosis.users
DROP CONSTRAINT IF EXISTS users_function_check;

ALTER TABLE sc_student_diagnosis.users
DROP CONSTRAINT IF EXISTS check_admin_school;

-- 2. Promover a conta principal a superadministrador.
UPDATE sc_student_diagnosis.users
SET
    function = 'superadmin',
    school_id = NULL,
    updated_at = NOW()
WHERE email = 'admin@escola.com';

-- 3. Vincular o administrador institucional à escola correta.
UPDATE sc_student_diagnosis.users
SET
    function = 'admin',
    school_id = (
        SELECT id
        FROM sc_student_diagnosis.schools
        WHERE inep_code = '35012345'
    ),
    updated_at = NOW()
WHERE email = 'jose.admin@escola.com';

-- 4. Validar os perfis permitidos.
ALTER TABLE sc_student_diagnosis.users
ADD CONSTRAINT users_function_check
CHECK (
    function IN (
        'aluno',
        'professor',
        'admin',
        'superadmin'
    )
);

-- 5. Validar os vínculos institucionais.
ALTER TABLE sc_student_diagnosis.users
ADD CONSTRAINT check_admin_school
CHECK (
    (function = 'admin' AND school_id IS NOT NULL)
    OR
    (function = 'superadmin' AND school_id IS NULL)
    OR
    (function IN ('aluno', 'professor'))
);