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
  idx_socioeconomic_digital = 3.43,
  idx_work_overload = 2.50,
  idx_school_bonding = 0.00,
  idx_cultural_capital = 5.00,
  cluster_id = 2,
  pedagogical_profile = 'Perfil Trabalhador / Vulnerabilidade Econômica',
  pca_1 = -4.050,
  pca_2 = -0.228,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'henrygabriel.sousa@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 7.43,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 1.341,
  pca_2 = -0.268,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'joaolucas.caldeira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 5.73,
  idx_work_overload = 0.00,
  idx_school_bonding = 10.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 1.492,
  pca_2 = 0.238,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'yan.camara@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 6.51,
  idx_work_overload = 0.00,
  idx_school_bonding = 6.50,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.348,
  pca_2 = -1.593,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lorenzo.vasconcelos@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.53,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 7.50,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.180,
  pca_2 = 0.991,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lucas.moura@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.44,
  idx_work_overload = 0.00,
  idx_school_bonding = 5.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -0.689,
  pca_2 = -0.637,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'rodrigo.barros@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 5.30,
  idx_work_overload = 0.00,
  idx_school_bonding = 7.00,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -0.048,
  pca_2 = -1.093,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'francisco.daconceicao@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 7.43,
  idx_work_overload = 0.00,
  idx_school_bonding = 10.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 2.172,
  pca_2 = -0.500,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lavinia.alves@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 5.71,
  idx_work_overload = 0.00,
  idx_school_bonding = 10.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 1.484,
  pca_2 = 0.246,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'zoe.pastor@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.86,
  idx_work_overload = 0.00,
  idx_school_bonding = 3.00,
  idx_cultural_capital = 7.50,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -0.503,
  pca_2 = 1.398,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'diego.pires@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 4.50,
  idx_work_overload = 0.00,
  idx_school_bonding = 0.00,
  idx_cultural_capital = 7.50,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -0.781,
  pca_2 = 1.270,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'pietra.campos@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.64,
  idx_work_overload = 0.00,
  idx_school_bonding = 6.50,
  idx_cultural_capital = 7.50,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 0.031,
  pca_2 = 1.319,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'valentina.silveira@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 6.00,
  idx_work_overload = 0.00,
  idx_school_bonding = 7.00,
  idx_cultural_capital = 7.50,
  cluster_id = 1,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = 1.066,
  pca_2 = 0.270,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'miguel.rezende@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 3.89,
  idx_work_overload = 0.00,
  idx_school_bonding = 2.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -1.444,
  pca_2 = -0.248,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'mirella.alves@escola.com' LIMIT 1);

UPDATE student_analytics SET
  idx_socioeconomic_digital = 6.00,
  idx_work_overload = 0.00,
  idx_school_bonding = 2.33,
  idx_cultural_capital = 5.00,
  cluster_id = 0,
  pedagogical_profile = 'Perfil Engajado / Participativo e Cultural',
  pca_1 = -0.598,
  pca_2 = -1.164,
  updated_at = NOW()
WHERE answer_id =     (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'zoe.camara@escola.com' LIMIT 1);

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
     WHERE s.email = 'henrygabriel.sousa@escola.com' LIMIT 1),
    3.43, 2.50, 0.00, 5.00,
    2, 'Perfil Trabalhador / Vulnerabilidade Econômica', -4.050, -0.228
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'joaolucas.caldeira@escola.com' LIMIT 1),
    7.43, 0.00, 5.33, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 1.341, -0.268
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'yan.camara@escola.com' LIMIT 1),
    5.73, 0.00, 10.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 1.492, 0.238
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lorenzo.vasconcelos@escola.com' LIMIT 1),
    6.51, 0.00, 6.50, 5.00,
    0, 'Perfil Engajado / Participativo e Cultural', 0.348, -1.593
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lucas.moura@escola.com' LIMIT 1),
    4.53, 0.00, 5.33, 7.50,
    0, 'Perfil Engajado / Participativo e Cultural', 0.180, 0.991
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'rodrigo.barros@escola.com' LIMIT 1),
    4.44, 0.00, 5.33, 5.00,
    0, 'Perfil Engajado / Participativo e Cultural', -0.689, -0.637
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'francisco.daconceicao@escola.com' LIMIT 1),
    5.30, 0.00, 7.00, 5.00,
    0, 'Perfil Engajado / Participativo e Cultural', -0.048, -1.093
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'lavinia.alves@escola.com' LIMIT 1),
    7.43, 0.00, 10.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 2.172, -0.500
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'zoe.pastor@escola.com' LIMIT 1),
    5.71, 0.00, 10.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 1.484, 0.246
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'diego.pires@escola.com' LIMIT 1),
    3.86, 0.00, 3.00, 7.50,
    0, 'Perfil Engajado / Participativo e Cultural', -0.503, 1.398
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'pietra.campos@escola.com' LIMIT 1),
    4.50, 0.00, 0.00, 7.50,
    0, 'Perfil Engajado / Participativo e Cultural', -0.781, 1.270
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'valentina.silveira@escola.com' LIMIT 1),
    3.64, 0.00, 6.50, 7.50,
    0, 'Perfil Engajado / Participativo e Cultural', 0.031, 1.319
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'miguel.rezende@escola.com' LIMIT 1),
    6.00, 0.00, 7.00, 7.50,
    1, 'Perfil Engajado / Participativo e Cultural', 1.066, 0.270
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'mirella.alves@escola.com' LIMIT 1),
    3.89, 0.00, 2.33, 5.00,
    0, 'Perfil Engajado / Participativo e Cultural', -1.444, -0.248
  ),
  (
    (SELECT da.id FROM diagnosis_answer da
     JOIN student s ON da.student_id = s.id
     WHERE s.email = 'zoe.camara@escola.com' LIMIT 1),
    6.00, 0.00, 2.33, 5.00,
    0, 'Perfil Engajado / Participativo e Cultural', -0.598, -1.164
  )
) AS novos (answer_id, idx_socioeconomic_digital, idx_work_overload, idx_school_bonding, idx_cultural_capital, cluster_id, pedagogical_profile, pca_1, pca_2)
WHERE NOT EXISTS (
  SELECT 1
  FROM student_analytics AS existente
  WHERE existente.answer_id = novos.answer_id
);
