-- inserts_student_analytics.sql
-- Script gerado automaticamente pelo pipeline de análise de dados (analise_de_dados.py)
-- Persiste os indicadores calculados e o perfil de Machine Learning (K-Means/PCA)
--
-- Estratégia idempotente: atualiza as linhas existentes e insere apenas
-- as respostas que ainda não possuem analytics. Assim a sequence da
-- coluna identity não é consumida em execuções repetidas.

SET search_path TO sc_student_diagnosis, public;

-- 1) Atualiza registros já existentes (não consome identity).
UPDATE student_analytics SET
  idx_socioeconomic_digital = 6.16,
  idx_work_overload = 0.00,
  idx_school_bonding = 7.67,
  idx_cultural_capital = 2.50,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -2.338,
  pca_2 = 1.362,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'agatha.teixeira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 5.30,
  idx_work_overload = 0.00,
  idx_school_bonding = 2.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -0.732,
  pca_2 = -0.853,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'anabeatriz.pinto@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 2.36,
  idx_work_overload = 0.00,
  idx_school_bonding = 3.50,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = 0.244,
  pca_2 = 0.283,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'antonio.silveira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.51,
  idx_work_overload = 0.00,
  idx_school_bonding = 7.67,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -0.419,
  pca_2 = 1.317,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'bento.cunha@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 7.10,
  idx_work_overload = 0.00,
  idx_school_bonding = 4.67,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -1.516,
  pca_2 = -0.572,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'calebe.cassiano@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.86,
  idx_work_overload = 0.00,
  idx_school_bonding = 3.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.715,
  pca_2 = -0.998,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'diego.pires@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.53,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.335,
  pca_2 = -0.428,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'gabrielly.marques@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 0.43,
  idx_work_overload = 0.00,
  idx_school_bonding = 10.00,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = 0.537,
  pca_2 = 2.860,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'gael.ferreira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.87,
  idx_work_overload = 0.00,
  idx_school_bonding = 7.00,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -0.863,
  pca_2 = 0.750,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'henrygabriel.sousa@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 6.51,
  idx_work_overload = 0.00,
  idx_school_bonding = 6.50,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -1.417,
  pca_2 = 0.165,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lorenzo.vasconcelos@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.53,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.335,
  pca_2 = -0.428,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lucas.moura@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.29,
  idx_work_overload = 0.00,
  idx_school_bonding = 3.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.562,
  pca_2 = -1.110,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'maria.silveira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.50,
  idx_work_overload = 0.00,
  idx_school_bonding = 0.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.669,
  pca_2 = -2.122,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'pietra.campos@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.44,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -0.608,
  pca_2 = 0.328,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'rodrigo.barros@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.58,
  idx_work_overload = 0.00,
  idx_school_bonding = 2.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil em Desenvolvimento (Grupo 1)',
  pca_1 = -0.476,
  pca_2 = -0.666,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'samuel.martins@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 1.71,
  idx_work_overload = 10.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 7.50,
  cluster_id = 2,
  pedagogical_profile = 'Perfil Trabalhador / Vulnerabilidade Econômica',
  pca_1 = 3.861,
  pca_2 = 1.313,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'thales.novais@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.64,
  idx_work_overload = 0.00,
  idx_school_bonding = 6.50,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.581,
  pca_2 = 0.177,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'valentina.silveira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.50,
  idx_work_overload = 0.00,
  idx_school_bonding = 2.33,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.528,
  pca_2 = -1.378,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'vitorgabriel.cunha@escola.com' LIMIT 1);

-- 2) Insere somente respostas que ainda não possuem analytics.
INSERT INTO student_analytics (
  answer_id,
  idx_socioeconomic_digital,
  idx_work_overload,
  idx_school_bonding,
  idx_cultural_capital,
  cluster_id,
  pedagogical_profile,
  pca_1,
  pca_2
)
SELECT
  novos.answer_id,
  novos.idx_socioeconomic_digital,
  novos.idx_work_overload,
  novos.idx_school_bonding,
  novos.idx_cultural_capital,
  novos.cluster_id,
  novos.pedagogical_profile,
  novos.pca_1,
  novos.pca_2
FROM (
  VALUES
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'agatha.teixeira@escola.com' LIMIT 1),
    6.16, 0.00, 7.67, 2.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -2.338, 1.362
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'anabeatriz.pinto@escola.com' LIMIT 1),
    5.30, 0.00, 2.33, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.732, -0.853
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'antonio.silveira@escola.com' LIMIT 1),
    2.36, 0.00, 3.50, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', 0.244, 0.283
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'bento.cunha@escola.com' LIMIT 1),
    3.51, 0.00, 7.67, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.419, 1.317
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'calebe.cassiano@escola.com' LIMIT 1),
    7.10, 0.00, 4.67, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -1.516, -0.572
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'diego.pires@escola.com' LIMIT 1),
    3.86, 0.00, 3.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.715, -0.998
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'gabrielly.marques@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.335, -0.428
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'gael.ferreira@escola.com' LIMIT 1),
    0.43, 0.00, 10.00, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', 0.537, 2.860
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'henrygabriel.sousa@escola.com' LIMIT 1),
    4.87, 0.00, 7.00, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.863, 0.750
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lorenzo.vasconcelos@escola.com' LIMIT 1),
    6.51, 0.00, 6.50, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -1.417, 0.165
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lucas.moura@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.335, -0.428
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'maria.silveira@escola.com' LIMIT 1),
    4.29, 0.00, 3.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.562, -1.110
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'pietra.campos@escola.com' LIMIT 1),
    4.50, 0.00, 0.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.669, -2.122
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'rodrigo.barros@escola.com' LIMIT 1),
    4.44, 0.00, 5.33, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.608, 0.328
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'samuel.martins@escola.com' LIMIT 1),
    4.58, 0.00, 2.33, 5.00,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.476, -0.666
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'thales.novais@escola.com' LIMIT 1),
    1.71, 10.00, 5.33, 7.50,
    2, 'Perfil Trabalhador / Vulnerabilidade Econômica', 3.861, 1.313
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'valentina.silveira@escola.com' LIMIT 1),
    3.64, 0.00, 6.50, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.581, 0.177
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'vitorgabriel.cunha@escola.com' LIMIT 1),
    4.50, 0.00, 2.33, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 0.528, -1.378
  )
) AS novos (answer_id, idx_socioeconomic_digital, idx_work_overload, idx_school_bonding, idx_cultural_capital, cluster_id, pedagogical_profile, pca_1, pca_2)
WHERE NOT EXISTS (
  SELECT 1
  FROM student_analytics AS existente
  WHERE existente.answer_id = novos.answer_id
);
