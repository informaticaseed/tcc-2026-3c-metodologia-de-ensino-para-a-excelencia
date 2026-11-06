-- dados_revisada.sql
-- Dataset de Diagnóstico Estudantil: 9 alunos em 3 turmas.
--
-- OBSERVAÇÃO SOBRE AS SENHAS:
--   'hash_prof', 'hash_aluno' e 'hash_admin' são apenas marcadores.
--   database/init_db.py, na função corrigir_senhas_demo(), substitui esses
--   marcadores por hashes bcrypt da senha de demonstração "Teste@2026".
--   A conta admin@escola.com / admin123 NÃO está neste arquivo: ela é
--   criada por ensure_superadmin() em database/init_db.py.
--   As contas com is_active = FALSE usam a senha temporária em texto puro
--   "PrimeiroAcesso@2026" e precisam passar por /cadastro antes do login.
SET search_path TO sc_student_diagnosis, public;

-- 0) ESCOLAS
-- INSERT ... SELECT + WHERE NOT EXISTS evita consumir a sequence de
-- schools quando o seed é executado mais de uma vez.
INSERT INTO schools (name, inep_code)
SELECT novos.name, novos.inep_code
FROM (
    VALUES
('Escola Estadual Dom Pedro II', '35012345'),
('Colégio Técnico Estadual Alpha', '35098765')
) AS novos (name, inep_code)
WHERE NOT EXISTS (
    SELECT 1 FROM schools AS existentes
    WHERE existentes.inep_code = novos.inep_code
);

-- 1) USUÁRIOS
INSERT INTO users (username, email, password, function, is_active)
SELECT
    novos.username,
    novos.email,
    novos.password,
    novos.function,
    novos.is_active
FROM (
    VALUES
('prof_maria', 'maria.prof@escola.com', 'hash_prof', 'professor', TRUE),
('prof_mariana', 'mariana.prof@escola.com', 'hash_prof', 'professor', TRUE),
('henrygabriel_sousa', 'henrygabriel.sousa@escola.com', 'PrimeiroAcesso@2026', 'aluno', FALSE),
('yan_camara', 'yan.camara@escola.com', 'PrimeiroAcesso@2026', 'aluno', FALSE),
('joaolucas_caldeira', 'joaolucas.caldeira@escola.com', 'hash_aluno', 'aluno', TRUE),
('zoe_pastor', 'zoe.pastor@escola.com', 'hash_aluno', 'aluno', TRUE),
('lavinia_alves', 'lavinia.alves@escola.com', 'hash_aluno', 'aluno', TRUE),
('francisco_daconceicao', 'francisco.daconceicao@escola.com', 'hash_aluno', 'aluno', TRUE),
('mirella_alves', 'mirella.alves@escola.com', 'hash_aluno', 'aluno', TRUE),
('miguel_rezende', 'miguel.rezende@escola.com', 'hash_aluno', 'aluno', TRUE),
('zoe_camara', 'zoe.camara@escola.com', 'hash_aluno', 'aluno', TRUE)
) AS novos (username, email, password, function, is_active)
WHERE NOT EXISTS (
    SELECT 1 FROM users AS existentes
    WHERE existentes.email = novos.email
);

-- Administrador institucional
INSERT INTO users (
    username,
    email,
    password,
    function,
    school_id,
    is_active
)
SELECT
    'admin_jose',
    'jose.admin@escola.com',
    'hash_admin',
    'admin',
    (
        SELECT id
        FROM schools
        WHERE inep_code = '35012345'
    ),
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM users
    WHERE email = 'jose.admin@escola.com'
);

-- 2) PROFESSORES
INSERT INTO teachers (user_id, full_name, email)
SELECT novos.user_id, novos.full_name, novos.email
FROM (
    VALUES
((SELECT id FROM users WHERE email = 'maria.prof@escola.com' LIMIT 1), 'Maria da Silva Santos', 'maria.prof@escola.com'),
((SELECT id FROM users WHERE email = 'mariana.prof@escola.com' LIMIT 1), 'Mariana da Silva Santos', 'mariana.prof@escola.com')
) AS novos (user_id, full_name, email)
WHERE NOT EXISTS (
    SELECT 1 FROM teachers AS existentes
    WHERE existentes.email = novos.email
);

-- 2.1) VÍNCULO PROFESSOR - ESCOLAS
INSERT INTO teacher_schools (teacher_id, school_id) VALUES
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1)),
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1)),
((SELECT id FROM teachers WHERE email = 'mariana.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1))
ON CONFLICT DO NOTHING;

-- 2.2) TURMAS LECIONADAS PELOS PROFESSORES
INSERT INTO teacher_classes (teacher_id, school_id, grade, class) VALUES
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), '1º ano EM', 'A'),
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1), '2º ano EM', 'B'),
((SELECT id FROM teachers WHERE email = 'mariana.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), '3º ano EM', 'C')
ON CONFLICT (teacher_id, school_id, grade, class) DO NOTHING;

-- 3) ALUNOS
INSERT INTO student (user_id, school_id, full_name, email, grade, class)
SELECT
    novos.user_id,
    novos.school_id,
    novos.full_name,
    novos.email,
    novos.grade,
    novos.class
FROM (
    VALUES
((SELECT id FROM users WHERE email = 'henrygabriel.sousa@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Henry Gabriel Alves Sousa', 'henrygabriel.sousa@escola.com', '1º ano EM', 'A'),
((SELECT id FROM users WHERE email = 'yan.camara@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Yan da Cruz Câmara', 'yan.camara@escola.com', '1º ano EM', 'A'),
((SELECT id FROM users WHERE email = 'joaolucas.caldeira@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'João Lucas Sousa Caldeira', 'joaolucas.caldeira@escola.com', '1º ano EM', 'A'),
((SELECT id FROM users WHERE email = 'zoe.pastor@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1), 'Zoe Borges Pastor', 'zoe.pastor@escola.com', '2º ano EM', 'B'),
((SELECT id FROM users WHERE email = 'lavinia.alves@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1), 'Lavínia Andrade Alves', 'lavinia.alves@escola.com', '2º ano EM', 'B'),
((SELECT id FROM users WHERE email = 'francisco.daconceicao@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1), 'Francisco Cunha da Conceição', 'francisco.daconceicao@escola.com', '2º ano EM', 'B'),
((SELECT id FROM users WHERE email = 'mirella.alves@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Mirella Pereira Alves', 'mirella.alves@escola.com', '3º ano EM', 'C'),
((SELECT id FROM users WHERE email = 'miguel.rezende@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Miguel Silva Rezende', 'miguel.rezende@escola.com', '3º ano EM', 'C'),
((SELECT id FROM users WHERE email = 'zoe.camara@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Zoe Leão Câmara', 'zoe.camara@escola.com', '3º ano EM', 'C')
) AS novos (user_id, school_id, full_name, email, grade, class)
WHERE NOT EXISTS (
    SELECT 1 FROM student AS existentes
    WHERE existentes.email = novos.email
);

-- 4) PEDIDOS DE DIAGNÓSTICO
-- Insere somente pedidos que ainda não existem.
INSERT INTO diagnostic_requests (teacher_id, school_id, title, description, grade, class, status)
SELECT
    novos.teacher_id,
    novos.school_id,
    novos.title,
    novos.description,
    novos.grade,
    novos.class,
    novos.status
FROM (
    VALUES
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)', 'Mapeamento diagnóstico', '1º ano EM', 'A', 'aberto'),
((SELECT id FROM teachers WHERE email = 'maria.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35098765' LIMIT 1), 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)', 'Mapeamento diagnóstico', '2º ano EM', 'B', 'aberto'),
((SELECT id FROM teachers WHERE email = 'mariana.prof@escola.com' LIMIT 1), (SELECT id FROM schools WHERE inep_code = '35012345' LIMIT 1), 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)', 'Mapeamento diagnóstico', '3º ano EM', 'C', 'aberto')
) AS novos (teacher_id, school_id, title, description, grade, class, status)
WHERE NOT EXISTS (
    SELECT 1 FROM diagnostic_requests AS existentes
    WHERE existentes.school_id = novos.school_id
      AND existentes.title = novos.title
);

-- 5) RESPOSTAS
INSERT INTO diagnosis_answer (order_id, student_id)
SELECT novos.order_id, novos.student_id
FROM (
    VALUES
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'henrygabriel.sousa@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'yan.camara@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'joaolucas.caldeira@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), (SELECT id FROM student WHERE email = 'zoe.pastor@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), (SELECT id FROM student WHERE email = 'lavinia.alves@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), (SELECT id FROM student WHERE email = 'francisco.daconceicao@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'mirella.alves@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'miguel.rezende@escola.com' LIMIT 1)),
((SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), (SELECT id FROM student WHERE email = 'zoe.camara@escola.com' LIMIT 1))
) AS novos (order_id, student_id)
WHERE NOT EXISTS (
    SELECT 1 FROM diagnosis_answer AS existentes
    WHERE existentes.order_id = novos.order_id
      AND existentes.student_id = novos.student_id
);

-- 6) DADOS SOCIOECONÔMICOS
INSERT INTO socioeconomic_data (answer_id, family_income, works_besides_studying, work_hours_per_week, parents_education, has_internet_at_home, has_computer_at_home)
SELECT
    novos.answer_id,
    novos.family_income,
    novos.works_besides_studying,
    novos.work_hours_per_week,
    novos.parents_education,
    novos.has_internet_at_home,
    novos.has_computer_at_home
FROM (
    VALUES
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'henrygabriel.sousa@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Até 1 salário mínimo', TRUE, 10, 'Ensino fundamental incompleto', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'yan.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Entre 2 e 4 salários mínimos', FALSE, NULL, 'Ensino médio incompleto', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'joaolucas.caldeira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Acima de 6 salários mínimos', FALSE, NULL, 'Ensino fundamental incompleto', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.pastor@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Acima de 6 salários mínimos', FALSE, NULL, 'Ensino médio completo', FALSE, FALSE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'lavinia.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Acima de 6 salários mínimos', FALSE, NULL, 'Ensino fundamental incompleto', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'francisco.daconceicao@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Entre 2 e 4 salários mínimos', FALSE, NULL, 'Ensino fundamental completo', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'mirella.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Entre 4 e 6 salários mínimos', FALSE, NULL, 'Ensino médio incompleto', FALSE, FALSE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'miguel.rezende@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Até 1 salário mínimo', FALSE, NULL, 'Pós-graduação', TRUE, TRUE),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Até 1 salário mínimo', FALSE, NULL, 'Pós-graduação', TRUE, TRUE)
) AS novos (answer_id, family_income, works_besides_studying, work_hours_per_week, parents_education, has_internet_at_home, has_computer_at_home)
WHERE NOT EXISTS (
    SELECT 1 FROM socioeconomic_data AS existentes
    WHERE existentes.answer_id = novos.answer_id
);

-- 7) CONTEXTO CULTURAL
INSERT INTO cultural_context (answer_id, cultural_activities, community_cultural_tradition, role_family_community_training)
SELECT
    novos.answer_id,
    novos.cultural_activities,
    novos.community_cultural_tradition,
    novos.role_family_community_training
FROM (
    VALUES
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'henrygabriel.sousa@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Futebol e jogos digitais', 'Tradições de origem nordestina', 'Foca em disciplina e responsabilidade'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'yan.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Leitura, música e esportes', 'Festas de aniversário comunitárias', 'Apoia a criatividade e a continuidade dos estudos'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'joaolucas.caldeira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Desenho, cinema e fotografia', 'Quadrilha e danças regionais', 'Estimula a leitura e o diálogo em casa'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.pastor@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Desenho, cinema e fotografia', 'Quadrilha e danças regionais', 'Foca em disciplina e responsabilidade'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'lavinia.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Desenho, cinema e fotografia', 'Tradições de origem nordestina', 'Pouco envolvimento, mas apoia à distância'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'francisco.daconceicao@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Jogos de tabuleiro e leitura', 'Feira do bairro e festas de rua', 'Estimula a leitura e o diálogo em casa'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'mirella.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Capoeira e dança folclórica', 'Grupos culturais da igreja local', 'A família valoriza o trabalho e a cooperação'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'miguel.rezende@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Violão, canto e coral da igreja', 'Quadrilha e danças regionais', 'Estimula a leitura e o diálogo em casa'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Futebol e jogos digitais', 'Tradições de origem nordestina', 'Apoia a criatividade e a continuidade dos estudos')
) AS novos (answer_id, cultural_activities, community_cultural_tradition, role_family_community_training)
WHERE NOT EXISTS (
    SELECT 1 FROM cultural_context AS existentes
    WHERE existentes.answer_id = novos.answer_id
);

-- 8) EXPERIÊNCIAS ESCOLARES
INSERT INTO school_experiences (answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties)
SELECT
    novos.answer_id,
    novos.teachers_relations,
    novos.opinion_is_heard_at_school,
    novos.learning_difficulties
FROM (
    VALUES
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'henrygabriel.sousa@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Difícil, falta diálogo com alguns professores', FALSE, 'Falta de concentração e motivação'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'yan.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Excelente, me sinto apoiada', TRUE, 'Metodologias muito rápidas em algumas disciplinas'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'joaolucas.caldeira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Regular, depende muito do professor', TRUE, 'Conciliar trabalho e escola'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.pastor@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Excelente, me sinto apoiada', TRUE, 'Falta de apoio familiar nos estudos'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'lavinia.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Muito boa e acolhedora', TRUE, 'Metodologias muito rápidas em algumas disciplinas'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'francisco.daconceicao@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Excelente, me sinto apoiada', FALSE, 'Dificuldade em matemática e falta de materiais'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'mirella.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Razoável, com alguns conflitos pontuais', FALSE, 'Falta de concentração e motivação'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'miguel.rezende@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Excelente, me sinto apoiada', FALSE, 'Falta de concentração e motivação'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Regular, depende muito do professor', FALSE, 'Falta de concentração e motivação')
) AS novos (answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties)
WHERE NOT EXISTS (
    SELECT 1 FROM school_experiences AS existentes
    WHERE existentes.answer_id = novos.answer_id
);

-- 9) EXPECTATIVAS E SONHOS
INSERT INTO expectations_dreams (answer_id, personal_professional_goals, support_that_the_school_should_offer)
SELECT
    novos.answer_id,
    novos.personal_professional_goals,
    novos.support_that_the_school_should_offer
FROM (
    VALUES
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'henrygabriel.sousa@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Concluir os estudos e abrir um negócio próprio', 'Programas de mentoria com profissionais da área'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'yan.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Concluir os estudos e abrir um negócio próprio', 'Cursos técnicos e apoio para conciliar estudo e trabalho'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'joaolucas.caldeira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 1º ano EM A (Escola Estadual Dom Pedro II)' LIMIT 1), 'Trabalhar com música e artes', 'Mais orientação vocacional e reforço escolar'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.pastor@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Concluir os estudos e abrir um negócio próprio', 'Projetos, laboratório de informática e orientação profissional'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'lavinia.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Fazer medicina e ajudar a comunidade', 'Programas de mentoria com profissionais da área'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'francisco.daconceicao@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 2º ano EM B (Colégio Técnico Estadual Alpha)' LIMIT 1), 'Fazer medicina e ajudar a comunidade', 'Projetos, laboratório de informática e orientação profissional'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'mirella.alves@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Fazer medicina e ajudar a comunidade', 'Projetos, laboratório de informática e orientação profissional'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'miguel.rezende@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Ser professor e contribuir com a educação', 'Projetos, laboratório de informática e orientação profissional'),
((SELECT da.id FROM diagnosis_answer da JOIN student s ON da.student_id = s.id JOIN diagnostic_requests p ON da.order_id = p.id WHERE s.email = 'zoe.camara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre - 3º ano EM C (Escola Estadual Dom Pedro II)' LIMIT 1), 'Entrar na universidade e trabalhar com saúde', 'Psicólogo escolar e espaço de escuta')
) AS novos (answer_id, personal_professional_goals, support_that_the_school_should_offer)
WHERE NOT EXISTS (
    SELECT 1 FROM expectations_dreams AS existentes
    WHERE existentes.answer_id = novos.answer_id
);
