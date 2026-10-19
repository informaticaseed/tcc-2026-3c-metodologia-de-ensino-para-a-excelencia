import database
import bcrypt


class UserAlreadyExistsError(Exception):
    pass


def get_user_uuid(email):
    """Busca o UUID do usuário pelo email."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s;
                """,
                (email,)
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def create_account(username, email, password, role="aluno"):
    """
    Cria uma nova conta na tabela users e sincroniza com student ou teachers dependendo do perfil.
    Papéis válidos no banco: 'aluno', 'professor', 'admin'.
    """
    if get_user_uuid(email) is not None:
        raise UserAlreadyExistsError("User already exists")

    # Mapeia papéis comuns vindos do formulário
    role_normalized = role.lower().strip()
    if role_normalized in ['estudante', 'aluno']:
        db_role = 'aluno'
    elif role_normalized in ['professor', 'docente']:
        db_role = 'professor'
    elif role_normalized == 'admin':
        db_role = 'admin'
    else:
        db_role = 'aluno'

    passwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Inserir em users
            cur.execute(
                """
                INSERT INTO users (name_user, email, password, function)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (username.strip(), email.strip().lower(), passwd_hash, db_role)
            )
            user_id = cur.fetchone()[0]

            # 2. Inserir na tabela específica do perfil correspondente
            if db_role == 'aluno':
                cur.execute(
                    """
                    INSERT INTO student (user_id, full_name, email, grade, class)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET user_id = EXCLUDED.user_id;
                    """,
                    (user_id, username.strip(), email.strip().lower(), 'Não definida', 'A')
                )
            elif db_role == 'professor':
                cur.execute(
                    """
                    INSERT INTO teachers (user_id, full_name, email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET user_id = EXCLUDED.user_id;
                    """,
                    (user_id, username.strip(), email.strip().lower())
                )

        conn.commit()
        return user_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def authenticate_user(uuid, password):
    """Autentica o usuário pelo UUID e senha em texto plano."""
    if not uuid:
        return None

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name_user, email, function, password
                FROM users
                WHERE id = %s;
                """,
                (uuid,)
            )
            result = cur.fetchone()

        if result is None:
            return None

        user_id, name, user_email, role, passwrd_hash = result

        # Validação do bcrypt
        if isinstance(passwrd_hash, str):
            passwrd_hash_bytes = passwrd_hash.encode("utf-8")
        else:
            passwrd_hash_bytes = bytes(passwrd_hash)

        # Suporta verificação de hash bcrypt ou comparação direta para usuários legados/seeds
        valid = False
        try:
            valid = bcrypt.checkpw(password.encode("utf-8"), passwrd_hash_bytes)
        except ValueError:
            # Fallback caso a senha inicial no banco tenha sido inserida em texto puro (ex: hash_aluno)
            valid = (password == passwrd_hash)

        if not valid:
            return None

        return {
            "id": str(user_id),
            "nome": name,
            "email": user_email,
            "perfil": role
        }
    finally:
        conn.close()


def get_all_users():
    """Retorna a lista de usuários para o painel de administração."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name_user, email, function, created_at
                FROM users
                ORDER BY created_at DESC;
                """
            )
            rows = cur.fetchall()
            return [
                {
                    "id": str(r[0])[:8],
                    "nome": r[1],
                    "email": r[2],
                    "perfil": r[3],
                    "criado_em": r[4].strftime("%d/%m/%Y %H:%M") if r[4] else ""
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_users_statistics():
    """Retorna métricas agregadas de usuários."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            total_usuarios = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM teachers;")
            total_professores = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM student;")
            total_estudantes = cur.fetchone()[0]

            return {
                "total_usuarios": total_usuarios,
                "total_professores": total_professores,
                "total_estudantes": total_estudantes
            }
    finally:
        conn.close()


def get_student_analytics_summary():
    """Retorna os dados detalhados e médias de student_analytics para o dashboard pedagógico."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    sa.id,
                    s.full_name,
                    s.grade,
                    s.class,
                    sa.idx_socioeconomic_digital,
                    sa.idx_work_overload,
                    sa.idx_school_bonding,
                    sa.idx_political_engagement,
                    sa.idx_cultural_capital,
                    sa.cluster_id,
                    sa.pedagogical_profile,
                    sa.pca_1,
                    sa.pca_2
                FROM student_analytics sa
                JOIN diagnosis_answer da ON da.id = sa.answer_id
                JOIN student s ON s.id = da.student_id
                ORDER BY s.grade, s.class, s.full_name;
                """
            )
            rows = cur.fetchall()

            students_data = []
            for r in rows:
                students_data.append({
                    "id": r[0],
                    "nome": r[1],
                    "serie": r[2],
                    "turma": r[3],
                    "idx_socio": float(r[4]) if r[4] is not None else 0.0,
                    "idx_trabalho": float(r[5]) if r[5] is not None else 0.0,
                    "idx_vinculo": float(r[6]) if r[6] is not None else 0.0,
                    "idx_politico": float(r[7]) if r[7] is not None else 0.0,
                    "idx_cultural": float(r[8]) if r[8] is not None else 0.0,
                    "cluster_id": r[9],
                    "perfil": r[10],
                    "pca_1": float(r[11]) if r[11] is not None else 0.0,
                    "pca_2": float(r[12]) if r[12] is not None else 0.0,
                })

            # Médias globais
            if students_data:
                n = len(students_data)
                avg_socio = round(sum(s["idx_socio"] for s in students_data) / n, 2)
                avg_trabalho = round(sum(s["idx_trabalho"] for s in students_data) / n, 2)
                avg_vinculo = round(sum(s["idx_vinculo"] for s in students_data) / n, 2)
                avg_politico = round(sum(s["idx_politico"] for s in students_data) / n, 2)
                avg_cultural = round(sum(s["idx_cultural"] for s in students_data) / n, 2)
            else:
                avg_socio = avg_trabalho = avg_vinculo = avg_politico = avg_cultural = 0.0

            # Contagem de perfis pedagógicos
            perfis_count = {}
            for s in students_data:
                p = s["perfil"]
                perfis_count[p] = perfis_count.get(p, 0) + 1

            return {
                "students": students_data,
                "total_diagnosticados": len(students_data),
                "medias": {
                    "socio": avg_socio,
                    "trabalho": avg_trabalho,
                    "vinculo": avg_vinculo,
                    "politico": avg_politico,
                    "cultural": avg_cultural
                },
                "perfis_count": perfis_count
            }
    finally:
        conn.close()


def get_student_by_user_id(user_id):
    """Busca o registro de estudante vinculado ao user_id."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, grade, class
                FROM student
                WHERE user_id = %s
                LIMIT 1;
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "email": row[2],
                    "grade": row[3],
                    "class": row[4]
                }
            return None
    finally:
        conn.close()


def get_available_diagnostic_request(student_id):
    """Busca um pedido de diagnóstico aberto e verifica se o aluno já respondeu."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Pega os dados do estudante
            cur.execute("SELECT grade, class FROM student WHERE id = %s;", (student_id,))
            st_info = cur.fetchone()

            # 2. Busca pedido aberto compatível ou o primeiro aberto
            if st_info and st_info[0] != 'Não definida':
                cur.execute(
                    """
                    SELECT id, title, description, grade, class
                    FROM diagnostic_requests
                    WHERE status = 'aberto' AND grade = %s AND class = %s
                    ORDER BY id DESC LIMIT 1;
                    """,
                    (st_info[0], st_info[1])
                )
                req = cur.fetchone()
            else:
                req = None

            if not req:
                cur.execute(
                    """
                    SELECT id, title, description, grade, class
                    FROM diagnostic_requests
                    WHERE status = 'aberto'
                    ORDER BY id ASC LIMIT 1;
                    """
                )
                req = cur.fetchone()

            if not req:
                return None

            order_id = req[0]

            # 3. Verifica se já respondeu
            cur.execute(
                """
                SELECT id, send_date FROM diagnosis_answer
                WHERE order_id = %s AND student_id = %s;
                """,
                (order_id, student_id)
            )
            ans = cur.fetchone()

            return {
                "id": order_id,
                "titulo": req[1],
                "descricao": req[2],
                "serie": req[3],
                "turma": req[4],
                "respondido": ans is not None,
                "data_envio": ans[1].strftime("%d/%m/%Y às %H:%M") if ans else None
            }
    finally:
        conn.close()


def save_questionnaire_response(student_id, order_id, form_data):
    """
    Grava as respostas do questionário do estudante em todas as tabelas dimensionais
    respeitando o schema relacional PostgreSQL.
    """
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Atualizar série e turma do estudante se informadas
            serie = form_data.get('serie')
            turma = form_data.get('turma')
            if serie and turma:
                cur.execute(
                    """
                    UPDATE student
                    SET grade = %s, class = %s, updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (serie, turma, student_id)
                )

            # 2. Criar ou atualizar cabeçalho de resposta (diagnosis_answer)
            cur.execute(
                """
                INSERT INTO diagnosis_answer (order_id, student_id, send_date)
                VALUES (%s, %s, NOW())
                ON CONFLICT (order_id, student_id) DO UPDATE SET send_date = NOW()
                RETURNING id;
                """,
                (order_id, student_id)
            )
            answer_id = cur.fetchone()[0]

            # 3. Dados socioeconômicos (socioeconomic_data)
            family_income = form_data.get('family_income')
            works = form_data.get('works_besides_studying') == 'sim'
            work_hours = int(form_data.get('work_hours_per_week', 0) or 0) if works else 0
            parents_edu = form_data.get('parents_education')
            has_internet = form_data.get('has_internet_at_home') == 'sim'
            has_computer = form_data.get('has_computer_at_home') == 'sim'

            cur.execute(
                """
                INSERT INTO socioeconomic_data (
                    answer_id, family_income, works_besides_studying, work_hours_per_week,
                    parents_education, has_internet_at_home, has_computer_at_home, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (answer_id) DO UPDATE SET
                    family_income = EXCLUDED.family_income,
                    works_besides_studying = EXCLUDED.works_besides_studying,
                    work_hours_per_week = EXCLUDED.work_hours_per_week,
                    parents_education = EXCLUDED.parents_education,
                    has_internet_at_home = EXCLUDED.has_internet_at_home,
                    has_computer_at_home = EXCLUDED.has_computer_at_home,
                    updated_at = NOW();
                """,
                (answer_id, family_income, works, work_hours, parents_edu, has_internet, has_computer)
            )

            # 4. Vivência escolar (school_experiences)
            teachers_relations = form_data.get('teachers_relations')
            opinion_heard = form_data.get('opinion_is_heard_at_school') == 'sim'
            learning_diff = form_data.get('learning_difficulties', '')

            cur.execute(
                """
                INSERT INTO school_experiences (
                    answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties, updated_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (answer_id) DO UPDATE SET
                    teachers_relations = EXCLUDED.teachers_relations,
                    opinion_is_heard_at_school = EXCLUDED.opinion_is_heard_at_school,
                    learning_difficulties = EXCLUDED.learning_difficulties,
                    updated_at = NOW();
                """,
                (answer_id, teachers_relations, opinion_heard, learning_diff)
            )

            # 5. Expectativas e sonhos (expectations_dreams)
            goals = form_data.get('personal_professional_goals', '')
            school_support = form_data.get('support_that_the_school_should_offer', '')

            cur.execute(
                """
                INSERT INTO expectations_dreams (
                    answer_id, personal_professional_goals, support_that_the_school_should_offer, updated_at
                ) VALUES (%s, %s, %s, NOW())
                ON CONFLICT (answer_id) DO UPDATE SET
                    personal_professional_goals = EXCLUDED.personal_professional_goals,
                    support_that_the_school_should_offer = EXCLUDED.support_that_the_school_should_offer,
                    updated_at = NOW();
                """,
                (answer_id, goals, school_support)
            )

            # 6. Contexto cultural (cultural_context)
            cultural_acts = form_data.get('cultural_activities', '')
            comm_trad = form_data.get('community_cultural_tradition', '')
            fam_role = form_data.get('role_family_community_training', '')

            cur.execute(
                """
                INSERT INTO cultural_context (
                    answer_id, cultural_activities, community_cultural_tradition, role_family_community_training, updated_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (answer_id) DO UPDATE SET
                    cultural_activities = EXCLUDED.cultural_activities,
                    community_cultural_tradition = EXCLUDED.community_cultural_tradition,
                    role_family_community_training = EXCLUDED.role_family_community_training,
                    updated_at = NOW();
                """,
                (answer_id, cultural_acts, comm_trad, fam_role)
            )

            # 7. Dimensão política e cívica (political_dimension)
            follows_pol = form_data.get('follows_politics_society_news') == 'sim'
            part_movement = form_data.get('participated_in_social_movement') == 'sim'
            edu_role = form_data.get('role_education_social_transformation', '')

            cur.execute(
                """
                INSERT INTO political_dimension (
                    answer_id, follows_politics_society_news, participated_in_social_movement,
                    role_education_social_transformation, updated_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (answer_id) DO UPDATE SET
                    follows_politics_society_news = EXCLUDED.follows_politics_society_news,
                    participated_in_social_movement = EXCLUDED.participated_in_social_movement,
                    role_education_social_transformation = EXCLUDED.role_education_social_transformation,
                    updated_at = NOW();
                """,
                (answer_id, follows_pol, part_movement, edu_role)
            )

        conn.commit()
        return answer_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
