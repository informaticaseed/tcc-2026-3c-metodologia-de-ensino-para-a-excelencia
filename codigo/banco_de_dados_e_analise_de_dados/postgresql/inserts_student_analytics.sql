-- inserts_student_analytics.sql
-- Script gerado automaticamente pelo pipeline de análise de dados (analise_de_dados.py)
-- Persiste os indicadores calculados e o perfil de Machine Learning (K-Means/PCA)

SET search_path TO sc_student_diagnosis, sc_diagnostico_estudantil, public;

INSERT INTO student_analytics (
  answer_id,
  idx_socioeconomic_digital,
  idx_work_overload,
  idx_school_bonding,
  idx_political_engagement,
  idx_cultural_capital,
  cluster_id,
  pedagogical_profile,
  pca_1,
  pca_2
)
VALUES
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'henrygabriel.sousa@escola.com' LIMIT 1),
    4.23, 5.00, 0.00, 10.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.344, -2.806
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'yan.camara@escola.com' LIMIT 1),
    5.73, 0.00, 2.33, 0.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', 0.295, -1.037
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'joaolucas.caldeira@escola.com' LIMIT 1),
    4.15, 0.00, 7.00, 0.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.053, 2.072
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'zoe.pastor@escola.com' LIMIT 1),
    2.79, 10.00, 5.33, 5.00, 5.00,
    1, 'Perfil Trabalhador / Vulnerabilidade Econômica', -1.839, 1.022
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'lavinia.alves@escola.com' LIMIT 1),
    4.87, 0.00, 2.33, 5.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.945, -0.346
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'francisco.daconceicao@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 5.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', 0.108, -0.173
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'mirella.alves@escola.com' LIMIT 1),
    4.58, 0.00, 2.33, 10.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 1.259, -0.773
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'miguel.rezende@escola.com' LIMIT 1),
    4.50, 0.00, 2.33, 0.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.311, -0.976
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'zoe.camara@escola.com' LIMIT 1),
    1.71, 10.00, 5.33, 0.00, 7.50,
    1, 'Perfil Trabalhador / Vulnerabilidade Econômica', -3.445, 0.426
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'manuela.damota@escola.com' LIMIT 1),
    7.10, 0.00, 4.67, 5.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 2.003, 0.517
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'anthonygabriel.castro@escola.com' LIMIT 1),
    2.36, 0.00, 3.50, 0.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.768, 0.706
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'lavinia.damota@escola.com' LIMIT 1),
    4.29, 0.00, 3.00, 0.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', -0.426, -0.688
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'leonardo.teixeira@escola.com' LIMIT 1),
    6.51, 0.00, 6.50, 5.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 1.680, 1.306
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'barbara.borges@escola.com' LIMIT 1),
    4.44, 0.00, 5.33, 5.00, 5.00,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.682, 0.922
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'gabrielly.fogaca@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 5.00, 7.50,
    0, 'Perfil em Desenvolvimento (Grupo 1)', 0.108, -0.173
  )
ON CONFLICT (answer_id) DO UPDATE SET
  idx_socioeconomic_digital = EXCLUDED.idx_socioeconomic_digital,
  idx_work_overload = EXCLUDED.idx_work_overload,
  idx_school_bonding = EXCLUDED.idx_school_bonding,
  idx_political_engagement = EXCLUDED.idx_political_engagement,
  idx_cultural_capital = EXCLUDED.idx_cultural_capital,
  cluster_id = EXCLUDED.cluster_id,
  pedagogical_profile = EXCLUDED.pedagogical_profile,
  pca_1 = EXCLUDED.pca_1,
  pca_2 = EXCLUDED.pca_2,
  updated_at = NOW();
