-- dados_revisada.sql
-- Dados de teste / semente para validação do fluxo:
-- 1. Criação de usuários (Admin, Professor, Alunos)
-- 2. Professor cria um Pedido de Diagnóstico para a Turma A do 8º ano
-- 3. Alunos respondem ao pedido com suas respectivas dimensões
-- 4. Sem IDs fixos (amarração 100% segura por chaves de negócio / subconsultas)

SET search_path TO sc_diagnostico_estudantil, public;

-- 1) Inserir Usuários de Autenticação
INSERT INTO users (user_name, email, password, function)
VALUES 
  ('admin_jose', 'jose.admin@escola.com', 'hash_da_senha_admin', 'admin'),
  ('prof_maria', 'maria.prof@escola.com', 'hash_da_senha_prof', 'professor'),
  ('ana_souza', 'ana.clara@escola.com', 'hash_da_senha_aluno', 'aluno'),
  ('bruno_lima', 'bruno.lima@escola.com', 'hash_da_senha_aluno', 'aluno'),
  ('carla_mendes', 'carla.pereira@escola.com', 'hash_da_senha_aluno', 'aluno')
ON CONFLICT (email) DO NOTHING;

-- 2) Inserir Professores vinculados ao seu usuário
INSERT INTO teachers (user_id, full_name, email)
VALUES
  (
    (SELECT id FROM users WHERE email = 'maria.prof@escola.com'),
    'Maria da Silva Santos',
    'maria.prof@escola.com'
  )
ON CONFLICT (email) DO NOTHING;

-- 3) Inserir Alunos vinculados aos seus respectivos usuários
INSERT INTO students (user_id, full_name, email, grade, class)
VALUES
  (
    (SELECT id FROM users WHERE email = 'ana.clara@escola.com'),
    'Ana Clara Souza',
    'ana.clara@escola.com',
    '8º ano',
    'A'
  ),
  (
    (SELECT id FROM users WHERE email = 'bruno.lima@escola.com'),
    'Bruno Henrique Lima',
    'bruno.lima@escola.com',
    '8º ano',
    'A'
  ),
  (
    (SELECT id FROM users WHERE email = 'carla.pereira@escola.com'),
    'Carla Mendes Pereira',
    'carla.pereira@escola.com',
    '8º ano',
    'A'
  )
ON CONFLICT (email) DO NOTHING;

-- 4) Professor cria um Pedido de Diagnóstico para o 8º ano A
INSERT INTO diagnostic_requests (teacher_id, title, descricao, grade, class, status)
VALUES
  (
    (SELECT id FROM teachers WHERE email = 'maria.prof@escola.com'),
    'Diagnóstico Inicial 2026 - 1º Bimestre',
    'Mapeamento socioeconômico, cultural e de expectativas para o início do ano letivo.',
    '8º ano',
    'A',
    'aberto'
  );

-- 5) Alunos entregam suas respostas para esse Pedido de Diagnóstico
INSERT INTO diagnosis_answer (order_id, student_id)
VALUES
  (
    (SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre' LIMIT 1),
    (SELECT id FROM students WHERE email = 'ana.clara@escola.com')
  ),
  (
    (SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre' LIMIT 1),
    (SELECT id FROM students WHERE email = 'bruno.lima@escola.com')
  ),
  (
    (SELECT id FROM diagnostic_requests WHERE title = 'Diagnóstico Inicial 2026 - 1º Bimestre' LIMIT 1),
    (SELECT id FROM students WHERE email = 'carla.pereira@escola.com')
  )
ON CONFLICT (order_id, student_id) DO NOTHING;

-- 6) Inserir Dimensão: Dados Socioeconômicos
INSERT INTO socioeconomic_data (
  answer_id, family_income, works_besides_studying, horas_trabalho_semana,
  parents_education, has_internet_at_home, has_computer_at_home
)
VALUES
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'até 2 salários mínimos', FALSE, NULL, 'Ensino médio completo', TRUE, TRUE
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'entre 2 e 4 salários mínimos', TRUE, 20, 'Ensino fundamental completo', TRUE, FALSE
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'acima de 4 salários mínimos', FALSE, NULL, 'Ensino superior completo', TRUE, TRUE
  )
ON CONFLICT (answer_id) DO NOTHING;

-- 7) Inserir Dimensão: Contexto Cultural
INSERT INTO cultural_context (
  answer_id, atividades_culturais, community_cultural_tradition, role_family_community_training
)
VALUES
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Leitura, música e esportes', 'Festa junina da comunidade', 'Incentiva os estudos e a participação em eventos locais'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Futebol e música', 'Culturas de origem familiar nordestina', 'A família valoriza o trabalho e a cooperação'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Teatro, leitura e dança', 'Participação em grupos culturais da igreja', 'Apoia a criatividade e a continuidade dos estudos'
  )
ON CONFLICT (answer_id) DO NOTHING;

-- 8) Inserir Dimensão: Dimensão Política
INSERT INTO political_dimension (
  answer_id, follows_politics_society_news, participated_in_social_movement,
  role_education_social_transformation
)
VALUES
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    TRUE, FALSE, 'A educação ajuda a formar cidadãos críticos e conscientes'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    FALSE, TRUE, 'A educação pode melhorar oportunidades e reduzir desigualdades'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    TRUE, TRUE, 'A escola é fundamental para transformar a sociedade por meio do conhecimento'
  )
ON CONFLICT (answer_id) DO NOTHING;

-- 9) Inserir Dimensão: Experiências Escolares
INSERT INTO school_experiences (
  answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties
)
VALUES
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Boa e respeitosa', TRUE, 'Falta de tempo para estudar em casa'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Razoável, com alguns conflitos', FALSE, 'Dificuldade em matemática e falta de materiais'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Muito boa e acolhedora', TRUE, 'Metodologias muito rápidas em algumas disciplinas'
  )
ON CONFLICT (answer_id) DO NOTHING;

-- 10) Inserir Dimensão: Expectativas e Sonhos
INSERT INTO expectations_dreams (
  answer_id, personal_professional_goals, support_that_the_school_should_offer
)
VALUES
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Entrar na universidade e trabalhar com saúde', 'Mais orientação vocacional e reforço escolar'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Concluir os estudos e abrir um negócio próprio', 'Cursos técnicos e apoio para conciliar estudo e trabalho'
  ),
  (
    (SELECT r.id FROM diagnosis_answer r 
     JOIN students a ON r.student_id = a.id 
     JOIN diagnostic_requests p ON r.order_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Seguir carreira na área de tecnologia', 'Projetos, laboratório de informática e orientação profissional'
  )
ON CONFLICT (answer_id) DO NOTHING;