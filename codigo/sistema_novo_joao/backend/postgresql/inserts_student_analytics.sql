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
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.129, -1.782
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'bento.cunha@escola.com' LIMIT 1),
    5.73, 0.00, 2.33, 0.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.455, -1.264
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'agatha.teixeira@escola.com' LIMIT 1),
    4.15, 0.00, 7.00, 0.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', -0.063, 1.776
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'gael.ferreira@escola.com' LIMIT 1),
    2.79, 10.00, 5.33, 5.00, 5.00,
    0, 'Perfil Trabalhador / Vulnerabilidade Econômica', -1.998, 1.732
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'anabeatriz.pinto@escola.com' LIMIT 1),
    4.87, 0.00, 2.33, 5.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', 1.041, 0.123
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'gabrielly.marques@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 5.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.184, -0.177
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'samuel.martins@escola.com' LIMIT 1),
    4.58, 0.00, 2.33, 10.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', 1.394, 0.134
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'vitorgabriel.cunha@escola.com' LIMIT 1),
    4.50, 0.00, 2.33, 0.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.216, -1.226
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'thales.novais@escola.com' LIMIT 1),
    1.71, 10.00, 5.33, 0.00, 7.50,
    0, 'Perfil Trabalhador / Vulnerabilidade Econômica', -3.643, 0.404
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'calebe.cassiano@escola.com' LIMIT 1),
    7.10, 0.00, 4.67, 5.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', 2.157, 0.873
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'antonio.silveira@escola.com' LIMIT 1),
    2.36, 0.00, 3.50, 0.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', -0.891, 0.608
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'maria.silveira@escola.com' LIMIT 1),
    4.29, 0.00, 3.00, 0.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.360, -0.986
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'lorenzo.vasconcelos@escola.com' LIMIT 1),
    6.51, 0.00, 6.50, 5.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', 1.757, 1.531
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'rodrigo.barros@escola.com' LIMIT 1),
    4.44, 0.00, 5.33, 5.00, 5.00,
    1, 'Perfil em Desenvolvimento (Grupo 2)', 0.678, 1.185
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'lucas.moura@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 5.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.184, -0.177
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'pietra.campos@escola.com' LIMIT 1),
    4.50, 0.00, 0.00, 5.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', 0.395, -2.040
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'diego.pires@escola.com' LIMIT 1),
    3.86, 0.00, 3.00, 0.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.594, -0.973
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN (SELECT id, email FROM student UNION ALL SELECT id, email FROM students) s ON da.student_id = s.id
     WHERE s.email = 'valentina.silveira@escola.com' LIMIT 1),
    3.64, 0.00, 6.50, 5.00, 7.50,
    2, 'Perfil em Desenvolvimento (Grupo 3)', -0.351, 0.259
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
