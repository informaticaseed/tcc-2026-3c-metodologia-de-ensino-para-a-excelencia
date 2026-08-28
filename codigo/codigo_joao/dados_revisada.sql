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
INSERT INTO respostas_diagnostico (pedido_id, aluno_id)
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
ON CONFLICT (pedido_id, aluno_id) DO NOTHING;

-- 6) Inserir Dimensão: Dados Socioeconômicos
INSERT INTO dados_socioeconomicos (
  resposta_id, renda_familiar, trabalha_alem_de_estudar, horas_trabalho_semana,
  escolaridade_pais_responsaveis, tem_internet_casa, tem_computador_casa
)
VALUES
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'até 2 salários mínimos', FALSE, NULL, 'Ensino médio completo', TRUE, TRUE
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'entre 2 e 4 salários mínimos', TRUE, 20, 'Ensino fundamental completo', TRUE, FALSE
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'acima de 4 salários mínimos', FALSE, NULL, 'Ensino superior completo', TRUE, TRUE
  )
ON CONFLICT (resposta_id) DO NOTHING;

-- 7) Inserir Dimensão: Contexto Cultural
INSERT INTO contexto_cultural (
  resposta_id, atividades_culturais, tradicao_cultural_comunitaria, papel_familia_comunidade_formacao
)
VALUES
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Leitura, música e esportes', 'Festa junina da comunidade', 'Incentiva os estudos e a participação em eventos locais'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Futebol e música', 'Culturas de origem familiar nordestina', 'A família valoriza o trabalho e a cooperação'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Teatro, leitura e dança', 'Participação em grupos culturais da igreja', 'Apoia a criatividade e a continuidade dos estudos'
  )
ON CONFLICT (resposta_id) DO NOTHING;

-- 8) Inserir Dimensão: Dimensão Política
INSERT INTO dimensao_politica (
  resposta_id, acompanha_noticias_politica_sociedade, participou_movimento_social,
  papel_educacao_transformacao_social
)
VALUES
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    TRUE, FALSE, 'A educação ajuda a formar cidadãos críticos e conscientes'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    FALSE, TRUE, 'A educação pode melhorar oportunidades e reduzir desigualdades'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    TRUE, TRUE, 'A escola é fundamental para transformar a sociedade por meio do conhecimento'
  )
ON CONFLICT (resposta_id) DO NOTHING;

-- 9) Inserir Dimensão: Experiências Escolares
INSERT INTO experiencias_escolares (
  resposta_id, relacao_professores, opiniao_e_ouvida_na_escola, dificuldades_aprendizado
)
VALUES
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Boa e respeitosa', TRUE, 'Falta de tempo para estudar em casa'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Razoável, com alguns conflitos', FALSE, 'Dificuldade em matemática e falta de materiais'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Muito boa e acolhedora', TRUE, 'Metodologias muito rápidas em algumas disciplinas'
  )
ON CONFLICT (resposta_id) DO NOTHING;

-- 10) Inserir Dimensão: Expectativas e Sonhos
INSERT INTO expectativas_sonhos (
  resposta_id, objetivos_pessoais_profissionais, apoio_que_a_escola_deveria_oferecer
)
VALUES
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'ana.clara@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Entrar na universidade e trabalhar com saúde', 'Mais orientação vocacional e reforço escolar'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'bruno.lima@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Concluir os estudos e abrir um negócio próprio', 'Cursos técnicos e apoio para conciliar estudo e trabalho'
  ),
  (
    (SELECT r.id FROM respostas_diagnostico r 
     JOIN students a ON r.aluno_id = a.id 
     JOIN diagnostic_requests p ON r.pedido_id = p.id 
     WHERE a.email = 'carla.pereira@escola.com' AND p.title = 'Diagnóstico Inicial 2026 - 1º Bimestre'),
    'Seguir carreira na área de tecnologia', 'Projetos, laboratório de informática e orientação profissional'
  )
ON CONFLICT (resposta_id) DO NOTHING;