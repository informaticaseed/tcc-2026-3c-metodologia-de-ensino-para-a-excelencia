import database
import bcrypt
from datetime import datetime

from academico import serie_valida, turma_valida


class UserAlreadyExistsError(Exception):
    pass


def get_user_uuid(identificador):
    """
    Busca o UUID do usuário por username ou e-mail.
    Retorna None se a conta estiver inativa (is_active = FALSE),
    pois contas não ativadas não podem fazer login.
    """
    identificador_limpo = identificador.strip().lower()

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM users
                WHERE is_active = TRUE
                  AND (
                    LOWER(email) = %s
                    OR LOWER(username) = %s
                  )
                LIMIT 1;
                """,
                (identificador_limpo, identificador_limpo)
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
                INSERT INTO users (username, email, password, function)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (username.strip(), email.strip().lower(), passwd_hash, db_role)
            )
            user_id = cur.fetchone()[0]

            # 2. Inserir na tabela específica do perfil correspondente.
            #    O UPDATE + INSERT ... WHERE NOT EXISTS evita consumir a
            #    sequence quando já existe um registro com o mesmo e-mail.
            email_normalizado = email.strip().lower()

            if db_role == 'aluno':
                cur.execute(
                    """
                    UPDATE student
                    SET user_id = %s
                    WHERE email = %s;
                    """,
                    (user_id, email_normalizado)
                )
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO student (user_id, full_name, email, grade, class)
                        SELECT %s, %s, %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM student WHERE email = %s
                        );
                        """,
                        (
                            user_id,
                            username.strip(),
                            email_normalizado,
                            'Não definida',
                            'A',
                            email_normalizado
                        )
                    )
            elif db_role == 'professor':
                cur.execute(
                    """
                    UPDATE teachers
                    SET user_id = %s
                    WHERE email = %s;
                    """,
                    (user_id, email_normalizado)
                )
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO teachers (user_id, full_name, email)
                        SELECT %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM teachers WHERE email = %s
                        );
                        """,
                        (
                            user_id,
                            username.strip(),
                            email_normalizado,
                            email_normalizado
                        )
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
                SELECT id, username, email, function, password
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
                SELECT id, COALESCE(username, username), email, function, created_at
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


def get_user_by_id(user_id):
    """Retorna dados do usuário, incluindo o vínculo escolar."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.email,
                    u.function,
                    u.school_id,
                    s.name,
                    u.is_active
                FROM users u
                LEFT JOIN schools s ON s.id = u.school_id
                WHERE u.id = %s
                LIMIT 1;
                """,
                (user_id,)
            )
            r = cur.fetchone()

            if not r:
                return None

            return {
                "id": str(r[0]),
                "username": r[1],
                "email": r[2],
                "perfil": r[3],
                "school_id": r[4],
                "escola": r[5],
                "is_active": r[6]
            }
    finally:
        conn.close()


def get_all_schools():
    """Lista as instituições de ensino com contadores de vínculos."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.inep_code,
                    s.created_at,
                    (
                        SELECT COUNT(*)
                        FROM users u
                        WHERE u.function = 'admin'
                          AND u.school_id = s.id
                    ) AS admins,
                    (
                        SELECT COUNT(DISTINCT t.id)
                        FROM teachers t
                        INNER JOIN teacher_schools ts
                            ON ts.teacher_id = t.id
                        WHERE ts.school_id = s.id
                    ) AS professores,
                    (
                        SELECT COUNT(*)
                        FROM student st
                        WHERE st.school_id = s.id
                    ) AS estudantes
                FROM schools s
                ORDER BY s.name;
                """
            )
            rows = cur.fetchall()

            return [
                {
                    "id": r[0],
                    "nome": r[1],
                    "inep": r[2],
                    "criada_em": (
                        r[3].strftime("%d/%m/%Y %H:%M") if r[3] else ""
                    ),
                    "admins": int(r[4] or 0),
                    "professores": int(r[5] or 0),
                    "estudantes": int(r[6] or 0)
                }
                for r in rows
            ]
    finally:
        conn.close()


def create_school(name, inep_code=None):
    """
    Cadastra uma instituição de ensino.

    A rota que chama esta função valida que o usuário é superadmin.
    O código INEP é obrigatório e deve ser único.
    """
    name = (name or "").strip()
    inep_code = (inep_code or "").strip()

    if not name:
        raise ValueError("Informe o nome da instituição de ensino.")

    if len(name) > 255:
        raise ValueError(
            "O nome da instituição deve ter no máximo 255 caracteres."
        )

    if not inep_code:
        raise ValueError("Informe o código INEP da instituição de ensino.")

    if len(inep_code) > 20:
        raise ValueError(
            "O código INEP deve ter no máximo 20 caracteres."
        )

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM schools
                WHERE inep_code = %s
                LIMIT 1;
                """,
                (inep_code,)
            )
            if cur.fetchone():
                raise ValueError(
                    "Já existe uma instituição com este código INEP."
                )

            cur.execute(
                """
                INSERT INTO schools (name, inep_code)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (name, inep_code)
            )
            school_id = cur.fetchone()[0]

        conn.commit()
        return school_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_users_for_actor(actor_user_id):
    """
    Lista os usuários que o ator pode administrar.

    - superadmin: todos os usuários do sistema;
    - admin: somente usuários vinculados à escola do próprio admin.
    """
    actor = get_user_by_id(actor_user_id)

    if not actor or actor["perfil"] not in ("admin", "superadmin"):
        return []

    filtro = ""
    params = []

    if actor["perfil"] == "admin":
        if not actor["school_id"]:
            return []

        filtro = """
            WHERE (
                (u.function = 'admin' AND u.school_id = %s)
                OR (
                    u.function = 'aluno'
                    AND EXISTS (
                        SELECT 1
                        FROM student st
                        WHERE st.user_id = u.id
                          AND st.school_id = %s
                    )
                )
                OR (
                    u.function = 'professor'
                    AND EXISTS (
                        SELECT 1
                        FROM teachers t
                        INNER JOIN teacher_schools ts
                            ON ts.teacher_id = t.id
                        WHERE t.user_id = u.id
                          AND ts.school_id = %s
                    )
                )
            )
        """
        params = [actor["school_id"]] * 3

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    u.id,
                    COALESCE(
                        (
                            SELECT st.full_name
                            FROM student st
                            WHERE st.user_id = u.id
                            LIMIT 1
                        ),
                        (
                            SELECT t.full_name
                            FROM teachers t
                            WHERE t.user_id = u.id
                            LIMIT 1
                        ),
                        u.username
                    ) AS nome,
                    u.username,
                    u.email,
                    u.function,
                    u.is_active,
                    u.created_at,
                    CASE
                        WHEN u.function = 'admin' THEN (
                            SELECT sc.name
                            FROM schools sc
                            WHERE sc.id = u.school_id
                        )
                        WHEN u.function = 'aluno' THEN (
                            SELECT sc.name
                            FROM student st
                            INNER JOIN schools sc
                                ON sc.id = st.school_id
                            WHERE st.user_id = u.id
                            LIMIT 1
                        )
                        WHEN u.function = 'professor' THEN (
                            SELECT string_agg(
                                sc.name, ', ' ORDER BY sc.name
                            )
                            FROM teachers t
                            INNER JOIN teacher_schools ts
                                ON ts.teacher_id = t.id
                            INNER JOIN schools sc
                                ON sc.id = ts.school_id
                            WHERE t.user_id = u.id
                        )
                        ELSE NULL
                    END AS escola
                FROM users u
                {filtro}
                ORDER BY u.created_at DESC;
                """,
                tuple(params)
            )
            rows = cur.fetchall()

            usuarios = [
                {
                    "id": str(r[0])[:8],
                    "nome": r[1],
                    "username": r[2],
                    "email": r[3],
                    "perfil": r[4],
                    "ativo": r[5],
                    "criado_em": (
                        r[6].strftime("%d/%m/%Y %H:%M") if r[6] else ""
                    ),
                    "escola": r[7]
                }
                for r in rows
            ]

            # O admin só enxerga a própria escola; não exibimos outros
            # vínculos que o usuário possa ter em instituições diferentes.
            if actor["perfil"] == "admin":
                for item in usuarios:
                    item["escola"] = actor["escola"]

            return usuarios
    finally:
        conn.close()


def get_dashboard_statistics(actor_user_id):
    """
    Estatísticas do painel conforme o nível de acesso.

    O superadmin enxerga o sistema inteiro; o admin enxerga apenas a
    própria escola.
    """
    actor = get_user_by_id(actor_user_id)

    vazio = {
        "total_usuarios": 0,
        "total_admins": 0,
        "total_professores": 0,
        "total_estudantes": 0,
        "total_escolas": 0
    }

    if not actor:
        return vazio

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            if actor["perfil"] == "superadmin":
                cur.execute(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM users),
                        (
                            SELECT COUNT(*)
                            FROM users
                            WHERE function = 'admin'
                        ),
                        (SELECT COUNT(*) FROM teachers),
                        (SELECT COUNT(*) FROM student),
                        (SELECT COUNT(*) FROM schools);
                    """
                )
                r = cur.fetchone()
                return {
                    "total_usuarios": int(r[0] or 0),
                    "total_admins": int(r[1] or 0),
                    "total_professores": int(r[2] or 0),
                    "total_estudantes": int(r[3] or 0),
                    "total_escolas": int(r[4] or 0)
                }

            if actor["perfil"] == "admin" and actor["school_id"]:
                cur.execute(
                    """
                    SELECT
                        (
                            SELECT COUNT(*)
                            FROM users
                            WHERE function = 'admin'
                              AND school_id = %s
                        ),
                        (
                            SELECT COUNT(DISTINCT t.id)
                            FROM teachers t
                            INNER JOIN teacher_schools ts
                                ON ts.teacher_id = t.id
                            WHERE ts.school_id = %s
                        ),
                        (
                            SELECT COUNT(*)
                            FROM student
                            WHERE school_id = %s
                        );
                    """,
                    (
                        actor["school_id"],
                        actor["school_id"],
                        actor["school_id"]
                    )
                )
                r = cur.fetchone()
                admins = int(r[0] or 0)
                professores = int(r[1] or 0)
                estudantes = int(r[2] or 0)

                return {
                    # Para o admin da escola, o total considera apenas os
                    # professores e estudantes vinculados à sua instituição.
                    "total_usuarios": professores + estudantes,
                    "total_admins": admins,
                    "total_professores": professores,
                    "total_estudantes": estudantes,
                    "total_escolas": 1
                }

            return vazio
    finally:
        conn.close()


def create_managed_user(
    actor_user_id,
    role,
    full_name,
    email,
    username,
    password,
    school_id=None,
    grade=None,
    school_class=None
):
    """
    Cria contas conforme o nível de acesso do ator.

    - superadmin cria administradores (sempre vinculados a uma escola);
    - admin cria professores e estudantes apenas na própria escola.

    Professores e estudantes são criados inativos, com senha temporária,
    e passam pelo fluxo de Primeiro Acesso. Administradores já são criados
    ativos, com senha definitiva em bcrypt.
    """
    actor = get_user_by_id(actor_user_id)

    if not actor:
        raise ValueError("Sessão inválida. Faça login novamente.")

    role = (role or "").strip().lower()
    role = {
        "estudante": "aluno",
        "docente": "professor"
    }.get(role, role)

    if actor["perfil"] == "superadmin":
        # O cadastro feito pelo superadmin é sempre de administrador.
        role = role or "admin"
        permitidos = {"admin"}
    elif actor["perfil"] == "admin":
        permitidos = {"aluno", "professor"}
    else:
        raise ValueError(
            "Seu perfil não tem permissão para cadastrar usuários."
        )

    if role not in permitidos:
        raise ValueError(
            "Seu perfil não pode cadastrar este tipo de usuário."
        )

    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    username = (username or "").strip()
    password = password or ""
    grade = (grade or "").strip()
    school_class = (school_class or "").strip()

    if not full_name:
        raise ValueError("Informe o nome completo.")

    if len(full_name) > 200:
        raise ValueError("O nome deve ter no máximo 200 caracteres.")

    if not email or "@" not in email:
        raise ValueError("Informe um e-mail válido.")

    if len(email) > 255:
        raise ValueError("O e-mail deve ter no máximo 255 caracteres.")

    if not username:
        raise ValueError("Informe o código de acesso (nome de usuário).")

    if len(username) > 100:
        raise ValueError(
            "O código de acesso deve ter no máximo 100 caracteres."
        )

    if len(password) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")

    if role == "aluno":
        if not grade:
            raise ValueError("Informe a série do estudante.")

        if not school_class:
            raise ValueError("Informe a turma do estudante.")

        if len(grade) > 50 or len(school_class) > 50:
            raise ValueError(
                "Série e turma devem ter no máximo 50 caracteres."
            )

        if not serie_valida(grade):
            raise ValueError(
                "Série inválida. Selecione uma série do Ensino Médio."
            )

        if not turma_valida(school_class):
            raise ValueError(
                "Turma inválida. Selecione uma turma cadastrada no sistema."
            )

    if actor["perfil"] == "admin":
        if not actor["school_id"]:
            raise ValueError(
                "Seu usuário não está vinculado a uma escola."
            )
        school_id = actor["school_id"]
    else:
        try:
            school_id = int(school_id)
        except (TypeError, ValueError):
            raise ValueError(
                "Selecione a instituição do administrador."
            )

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM users WHERE LOWER(email) = %s LIMIT 1;",
                (email,)
            )
            if cur.fetchone():
                raise ValueError(
                    "Já existe uma conta cadastrada com este e-mail."
                )

            cur.execute(
                "SELECT 1 FROM users WHERE LOWER(username) = %s LIMIT 1;",
                (username.lower(),)
            )
            if cur.fetchone():
                raise ValueError(
                    "Este código de acesso já está em uso."
                )

            cur.execute(
                "SELECT 1 FROM schools WHERE id = %s LIMIT 1;",
                (school_id,)
            )
            if not cur.fetchone():
                raise ValueError("Instituição de ensino não encontrada.")

            if role == "admin":
                passwd_hash = bcrypt.hashpw(
                    password.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                cur.execute(
                    """
                    INSERT INTO users (
                        username, email, password, function,
                        school_id, is_active
                    )
                    VALUES (%s, %s, %s, 'admin', %s, TRUE)
                    RETURNING id;
                    """,
                    (username, email, passwd_hash, school_id)
                )
            else:
                # Senha temporária em texto puro: o Primeiro Acesso ativa a
                # conta e o fluxo de perfil exige a definição de uma senha
                # definitiva em bcrypt.
                cur.execute(
                    """
                    INSERT INTO users (
                        username, email, password, function,
                        school_id, is_active
                    )
                    VALUES (%s, %s, %s, %s, NULL, FALSE)
                    RETURNING id;
                    """,
                    (username, email, password, role)
                )

            user_id = cur.fetchone()[0]

            if role == "aluno":
                cur.execute(
                    """
                    INSERT INTO student (
                        user_id, school_id, full_name, email, grade, class
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        user_id,
                        school_id,
                        full_name,
                        email,
                        grade,
                        school_class
                    )
                )
            elif role == "professor":
                cur.execute(
                    """
                    INSERT INTO teachers (user_id, full_name, email)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (user_id, full_name, email)
                )
                teacher_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO teacher_schools (teacher_id, school_id)
                    VALUES (%s, %s);
                    """,
                    (teacher_id, school_id)
                )

        conn.commit()
        return {
            "id": str(user_id),
            "username": username,
            "role": role,
            "ativo": role == "admin"
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_student_analytics_summary(teacher_user_id, order_id=None):
    """
    Retorna os resultados analíticos somente dos alunos que responderam
    aos diagnósticos vinculados ao professor.

    Quando ``order_id`` é informado, o resultado é restrito àquele pedido
    de diagnóstico. A cláusula sempre exige o vínculo com o professor,
    servindo também como validação de propriedade.
    """
    conn = database.get_connection()

    try:
        with conn.cursor() as cur:
            query = """
                SELECT
                    sa.id,
                    s.full_name,
                    s.grade,
                    s.class,
                    sa.idx_socioeconomic_digital,
                    sa.idx_work_overload,
                    sa.idx_school_bonding,
                    sa.idx_cultural_capital,
                    sa.cluster_id,
                    sa.pedagogical_profile,
                    sa.pca_1,
                    sa.pca_2,
                    dr.id,
                    dr.title

                FROM student_analytics sa

                INNER JOIN diagnosis_answer da
                    ON da.id = sa.answer_id

                INNER JOIN student s
                    ON s.id = da.student_id

                INNER JOIN diagnostic_requests dr
                    ON dr.id = da.order_id

                INNER JOIN teachers t
                    ON t.id = dr.teacher_id

                WHERE t.user_id = %s
            """

            params = [teacher_user_id]

            if order_id is not None:
                query += " AND dr.id = %s"
                params.append(int(order_id))

            query += " ORDER BY s.grade, s.class, s.full_name;"

            cur.execute(query, tuple(params))

            rows = cur.fetchall()

            students_data = []
            pedido_info = None

            for r in rows:
                if pedido_info is None:
                    pedido_info = {
                        "id": r[12],
                        "titulo": r[13]
                    }

                students_data.append({
                    "id": r[0],
                    "nome": r[1],
                    "serie": r[2],
                    "turma": r[3],
                    "idx_socio": float(r[4]) if r[4] is not None else 0.0,
                    "idx_trabalho": float(r[5]) if r[5] is not None else 0.0,
                    "idx_vinculo": float(r[6]) if r[6] is not None else 0.0,
                    "idx_cultural": float(r[7]) if r[7] is not None else 0.0,
                    "cluster_id": r[8],
                    "perfil": r[9],
                    "pca_1": float(r[10]) if r[10] is not None else 0.0,
                    "pca_2": float(r[11]) if r[11] is not None else 0.0,
                })

            # Médias calculadas somente com os alunos encontrados
            if students_data:
                n = len(students_data)

                avg_socio = round(
                    sum(s["idx_socio"] for s in students_data) / n, 2
                )
                avg_trabalho = round(
                    sum(s["idx_trabalho"] for s in students_data) / n, 2
                )
                avg_vinculo = round(
                    sum(s["idx_vinculo"] for s in students_data) / n, 2
                )
                avg_cultural = round(
                    sum(s["idx_cultural"] for s in students_data) / n, 2
                )
            else:
                avg_socio = 0.0
                avg_trabalho = 0.0
                avg_vinculo = 0.0
                avg_cultural = 0.0

            # Contagem dos perfis pedagógicos
            perfis_count = {}

            for s in students_data:
                p = s["perfil"]
                perfis_count[p] = perfis_count.get(p, 0) + 1

            return {
                "students": students_data,
                "total_diagnosticados": len(students_data),
                "pedido": pedido_info,
                "medias": {
                    "socio": avg_socio,
                    "trabalho": avg_trabalho,
                    "vinculo": avg_vinculo,
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


def get_teacher_by_user_id(user_id):
    """Busca o registro de professor vinculado ao user_id."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email
                FROM teachers
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
                    "email": row[2]
                }
            return None
    finally:
        conn.close()


def get_teacher_schools(teacher_id):
    """Retorna as escolas às quais o professor está vinculado."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.name, s.inep_code
                FROM teacher_schools ts
                INNER JOIN schools s ON s.id = ts.school_id
                WHERE ts.teacher_id = %s
                ORDER BY s.name;
                """,
                (teacher_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "nome": r[1],
                    "inep": r[2]
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_teacher_classes(teacher_id):
    """Retorna as turmas cadastradas para o professor."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT school_id, grade, class
                FROM teacher_classes
                WHERE teacher_id = %s
                ORDER BY grade, class;
                """,
                (teacher_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "school_id": r[0],
                    "grade": r[1],
                    "class": r[2]
                }
                for r in rows
            ]
    finally:
        conn.close()


def _formatar_data_hora(valor):
    if valor is None:
        return None
    return valor.strftime("%d/%m/%Y às %H:%M")


def get_teacher_diagnostic_requests(teacher_id):
    """Lista os pedidos de diagnóstico criados pelo professor."""
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    dr.id,
                    dr.title,
                    dr.description,
                    dr.grade,
                    dr.class,
                    CASE
                        WHEN dr.status = 'encerrado'
                          OR (
                              dr.closing_date IS NOT NULL
                              AND dr.closing_date <= NOW()
                          )
                        THEN 'encerrado'
                        WHEN dr.opening_date IS NOT NULL
                         AND dr.opening_date > NOW()
                        THEN 'aguardando'
                        ELSE 'aberto'
                    END AS status_efetivo,
                    dr.opening_date,
                    dr.closing_date,
                    s.name,
                    (
                        SELECT COUNT(*)
                        FROM diagnosis_answer da
                        WHERE da.order_id = dr.id
                    ) AS respostas,
                    (dr.closing_date IS NULL OR dr.closing_date > NOW()) AS prazo_aberto
                FROM diagnostic_requests dr
                INNER JOIN schools s ON s.id = dr.school_id
                WHERE dr.teacher_id = %s
                ORDER BY dr.opening_date DESC, dr.id DESC;
                """,
                (teacher_id,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "titulo": r[1],
                    "descricao": r[2],
                    "serie": r[3],
                    "turma": r[4],
                    "status": r[5],
                    "abertura": _formatar_data_hora(r[6]),
                    "encerramento": _formatar_data_hora(r[7]),
                    "escola": r[8],
                    "respostas": int(r[9] or 0),
                    "pode_reabrir": r[5] == 'encerrado' and bool(r[10])
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_teacher_diagnostic_request(teacher_user_id, order_id):
    """
    Busca um pedido específico garantindo que ele pertence ao professor.

    Retorna None quando o pedido não existe ou pertence a outro professor,
    permitindo que as rotas tratem o acesso como negado.
    """
    teacher = get_teacher_by_user_id(teacher_user_id)

    if not teacher:
        return None

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    dr.id,
                    dr.title,
                    dr.description,
                    dr.grade,
                    dr.class,
                    CASE
                        WHEN dr.status = 'encerrado'
                          OR (
                              dr.closing_date IS NOT NULL
                              AND dr.closing_date <= NOW()
                          )
                        THEN 'encerrado'
                        WHEN dr.opening_date IS NOT NULL
                         AND dr.opening_date > NOW()
                        THEN 'aguardando'
                        ELSE 'aberto'
                    END AS status_efetivo,
                    dr.opening_date,
                    dr.closing_date,
                    s.name,
                    (
                        SELECT COUNT(*)
                        FROM diagnosis_answer da
                        WHERE da.order_id = dr.id
                    ) AS respostas,
                    (dr.closing_date IS NULL OR dr.closing_date > NOW()) AS prazo_aberto
                FROM diagnostic_requests dr
                INNER JOIN schools s ON s.id = dr.school_id
                WHERE dr.id = %s AND dr.teacher_id = %s
                LIMIT 1;
                """,
                (int(order_id), teacher["id"])
            )
            r = cur.fetchone()

            if not r:
                return None

            return {
                "id": r[0],
                "titulo": r[1],
                "descricao": r[2],
                "serie": r[3],
                "turma": r[4],
                "status": r[5],
                "abertura": _formatar_data_hora(r[6]),
                "encerramento": _formatar_data_hora(r[7]),
                "escola": r[8],
                "respostas": int(r[9] or 0),
                "pode_reabrir": r[5] == 'encerrado' and bool(r[10])
            }
    finally:
        conn.close()


def create_diagnostic_request(
    teacher_user_id,
    school_id,
    title,
    description,
    grade,
    school_class,
    opening_date=None,
    closing_date=None
):
    """
    Cria um pedido de diagnóstico para o professor autenticado.

    O pedido é sempre criado com status 'aberto'. O encerramento pode ser
    feito manualmente em "Meus pedidos de diagnóstico" ou automaticamente
    quando a data de encerramento for atingida.
    """
    teacher = get_teacher_by_user_id(teacher_user_id)

    if not teacher:
        raise ValueError(
            "Perfil de professor não encontrado para este usuário."
        )

    title = (title or "").strip()
    description = (description or "").strip()
    grade = (grade or "").strip()
    school_class = (school_class or "").strip()

    if not title:
        raise ValueError("Informe o título do pedido de diagnóstico.")

    if len(title) > 200:
        raise ValueError("O título deve ter no máximo 200 caracteres.")

    if not grade:
        raise ValueError("Informe a série do pedido.")

    if len(grade) > 50:
        raise ValueError("A série deve ter no máximo 50 caracteres.")

    if not serie_valida(grade):
        raise ValueError(
            "Série inválida. Selecione uma série do Ensino Médio."
        )

    if not school_class:
        raise ValueError("Informe a turma do pedido.")

    if len(school_class) > 50:
        raise ValueError("A turma deve ter no máximo 50 caracteres.")

    if not turma_valida(school_class):
        raise ValueError(
            "Turma inválida. Selecione uma turma cadastrada no sistema."
        )

    if opening_date is None:
        opening_date = datetime.now()

    if closing_date is not None:
        if closing_date < opening_date:
            raise ValueError(
                "A data de encerramento não pode ser anterior à data de abertura."
            )

        if closing_date <= datetime.now():
            raise ValueError(
                "A data de encerramento deve ser posterior ao momento atual."
            )

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # O professor só pode abrir pedidos para escolas às quais está vinculado.
            cur.execute(
                """
                SELECT 1
                FROM teacher_schools
                WHERE teacher_id = %s AND school_id = %s;
                """,
                (teacher["id"], school_id)
            )

            if not cur.fetchone():
                raise ValueError(
                    "Você não está vinculado à escola selecionada."
                )

            cur.execute(
                """
                INSERT INTO diagnostic_requests (
                    teacher_id,
                    school_id,
                    title,
                    description,
                    grade,
                    class,
                    status,
                    opening_date,
                    closing_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'aberto', %s, %s)
                RETURNING id;
                """,
                (
                    teacher["id"],
                    school_id,
                    title,
                    description,
                    grade,
                    school_class,
                    opening_date,
                    closing_date
                )
            )

            new_id = cur.fetchone()[0]

        conn.commit()
        return new_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



def sincronizar_pedidos_vencidos():
    """
    Encerra automaticamente os pedidos cujo prazo de encerramento já
    passou. Retorna a lista de IDs atualizados.
    """
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE diagnostic_requests
                SET status = 'encerrado', updated_at = NOW()
                WHERE status = 'aberto'
                  AND closing_date IS NOT NULL
                  AND closing_date <= NOW()
                RETURNING id;
                """
            )
            ids = [row[0] for row in cur.fetchall()]

        conn.commit()
        return ids
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_diagnostic_request_status(teacher_user_id, order_id, new_status):
    """
    Encerra ou reabre um pedido de diagnóstico do próprio professor.

    A reabertura é permitida apenas enquanto a data de encerramento não
    tiver sido atingida.
    """
    new_status = (new_status or "").strip().lower()

    if new_status not in ("aberto", "encerrado"):
        raise ValueError("Situação inválida. Use 'aberto' ou 'encerrado'.")

    teacher = get_teacher_by_user_id(teacher_user_id)

    if not teacher:
        raise ValueError(
            "Perfil de professor não encontrado para este usuário."
        )

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, closing_date
                FROM diagnostic_requests
                WHERE id = %s AND teacher_id = %s
                FOR UPDATE;
                """,
                (int(order_id), teacher["id"])
            )
            row = cur.fetchone()

            if not row:
                raise ValueError(
                    "Pedido não encontrado ou não vinculado a você."
                )

            _, closing_date = row

            if new_status == "aberto" and closing_date is not None:
                agora = (
                    datetime.now(closing_date.tzinfo)
                    if closing_date.tzinfo else datetime.now()
                )

                if closing_date <= agora:
                    raise ValueError(
                        "O prazo de encerramento já passou. "
                        "Não é possível reabrir este pedido."
                    )

            cur.execute(
                """
                UPDATE diagnostic_requests
                SET status = %s, updated_at = NOW()
                WHERE id = %s AND teacher_id = %s;
                """,
                (new_status, int(order_id), teacher["id"])
            )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_available_diagnostic_requests(student_id):
    """
    Lista TODOS os pedidos de diagnóstico abertos compatíveis com a
    escola, a série e a turma do estudante.

    Diferentemente da versão anterior (que usava LIMIT 1), esta consulta
    permite que o aluno visualize e responda mais de um diagnóstico da
    sua turma. Pedidos já respondidos continuam na lista para que o
    aluno possa revisar ou atualizar suas respostas enquanto estiverem
    abertos.
    """
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Dados de vínculo do estudante
            cur.execute(
                "SELECT school_id, grade, class FROM student WHERE id = %s;",
                (student_id,)
            )
            st_info = cur.fetchone()

            # Sem vínculo de escola/série/turma não há diagnóstico disponível.
            # Importante: não há fallback para pedidos de outras turmas.
            if not st_info:
                return []

            school_id, grade, class_name = st_info

            if not school_id or not grade or not class_name or grade == 'Não definida':
                return []

            # 2. Pedidos abertos da turma + resposta do aluno (se existir)
            cur.execute(
                """
                SELECT
                    dr.id,
                    dr.title,
                    dr.description,
                    dr.grade,
                    dr.class,
                    dr.opening_date,
                    t.full_name,
                    sc.name,
                    da.id AS answer_id,
                    da.send_date
                FROM diagnostic_requests dr
                JOIN teachers t ON t.id = dr.teacher_id
                JOIN schools sc ON sc.id = dr.school_id
                LEFT JOIN diagnosis_answer da
                    ON da.order_id = dr.id
                   AND da.student_id = %s
                WHERE dr.status = 'aberto'
                  AND (dr.closing_date IS NULL OR dr.closing_date > NOW())
                  AND (dr.opening_date IS NULL OR dr.opening_date <= NOW())
                  AND dr.school_id = %s
                  AND dr.grade = %s
                  AND dr.class = %s
                ORDER BY
                    (da.id IS NOT NULL) ASC,
                    dr.opening_date DESC,
                    dr.id DESC;
                """,
                (student_id, school_id, grade, class_name)
            )
            rows = cur.fetchall()

            return [
                {
                    "id": row[0],
                    "titulo": row[1],
                    "descricao": row[2],
                    "serie": row[3],
                    "turma": row[4],
                    "aberto_em": _formatar_data_hora(row[5]),
                    "professor": row[6],
                    "escola": row[7],
                    "respondido": row[8] is not None,
                    "data_envio": _formatar_data_hora(row[9]),
                }
                for row in rows
            ]
    finally:
        conn.close()


def get_available_diagnostic_request(student_id, order_id=None):
    """
    Retorna um pedido aberto compatível com o estudante.

    - Sem `order_id`: retorna o primeiro disponível (compatibilidade com
      chamadas antigas).
    - Com `order_id`: retorna somente se ele estiver aberto e pertencer à
      escola/série/turma do aluno. Caso contrário, retorna None.
    """
    pedidos = get_available_diagnostic_requests(student_id)

    if order_id is None:
        return pedidos[0] if pedidos else None

    for pedido in pedidos:
        if pedido["id"] == order_id:
            return pedido

    return None


def _buscar_respostas_aluno(student_id, order_id=None):
    """
    Consulta as respostas do aluno, opcionalmente filtrando por pedido.
    Retorna uma lista de dicionários pronta para os templates.
    """
    filtro_pedido = ""
    parametros = [student_id]

    if order_id is not None:
        filtro_pedido = "AND da.order_id = %s"
        parametros.append(order_id)

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    da.id,
                    dr.id,
                    dr.title,
                    dr.description,
                    dr.grade,
                    dr.class,
                    CASE
                        WHEN dr.status = 'encerrado'
                          OR (
                              dr.closing_date IS NOT NULL
                              AND dr.closing_date <= NOW()
                          )
                        THEN 'encerrado'
                        WHEN dr.opening_date IS NOT NULL
                         AND dr.opening_date > NOW()
                        THEN 'aguardando'
                        ELSE 'aberto'
                    END AS status_efetivo,
                    dr.opening_date,
                    t.full_name,
                    sc.name,
                    da.send_date,
                    sd.family_income,
                    sd.works_besides_studying,
                    sd.work_hours_per_week,
                    sd.parents_education,
                    sd.has_internet_at_home,
                    sd.has_computer_at_home,
                    cc.cultural_activities,
                    cc.community_cultural_tradition,
                    cc.role_family_community_training,
                    se.teachers_relations,
                    se.opinion_is_heard_at_school,
                    se.learning_difficulties,
                    ed.personal_professional_goals,
                    ed.support_that_the_school_should_offer
                FROM diagnosis_answer da
                JOIN diagnostic_requests dr ON dr.id = da.order_id
                JOIN teachers t ON t.id = dr.teacher_id
                JOIN schools sc ON sc.id = dr.school_id
                LEFT JOIN socioeconomic_data sd ON sd.answer_id = da.id
                LEFT JOIN cultural_context cc ON cc.answer_id = da.id
                LEFT JOIN school_experiences se ON se.answer_id = da.id
                LEFT JOIN expectations_dreams ed ON ed.answer_id = da.id
                WHERE da.student_id = %s
                  {filtro_pedido}
                ORDER BY da.send_date DESC, da.id DESC;
                """,
                tuple(parametros)
            )

            respostas = []

            for row in cur.fetchall():
                respostas.append({
                    "answer_id": row[0],
                    "order_id": row[1],
                    "titulo": row[2],
                    "descricao": row[3],
                    "serie": row[4],
                    "turma": row[5],
                    "status_pedido": row[6],
                    "aberto_em": _formatar_data_hora(row[7]),
                    "professor": row[8],
                    "escola": row[9],
                    "data_envio": _formatar_data_hora(row[10]),

                    # Dados socioeconômicos
                    "renda_familiar": row[11],
                    "trabalha": bool(row[12]),
                    "horas_trabalho": row[13] or 0,
                    "escolaridade_pais": row[14],
                    "internet": row[15],
                    "computador": row[16],

                    # Contexto cultural
                    "atividades_culturais": row[17],
                    "tradicao_cultural": row[18],
                    "papel_familia": row[19],

                    # Experiências escolares
                    "relacao_professores": row[20],
                    "opiniao_ouvida": row[21],
                    "dificuldades": row[22],

                    # Expectativas e sonhos
                    "objetivos": row[23],
                    "apoio_escola": row[24],
                })

            return respostas
    finally:
        conn.close()


def get_student_answers(student_id):
    """Retorna todas as respostas já enviadas pelo estudante."""
    return _buscar_respostas_aluno(student_id)


def get_student_answer_detail(student_id, order_id):
    """
    Retorna a resposta do estudante para um pedido específico, ou None.
    Usada para pré-preencher o questionário e exibir o histórico.
    """
    respostas = _buscar_respostas_aluno(student_id, order_id)
    return respostas[0] if respostas else None


def save_questionnaire_response(student_id, order_id, form_data):
    """
    Grava as respostas do questionário do estudante,
    verificando se ele pode responder ao diagnóstico.
    """
    conn = database.get_connection()

    try:
        with conn.cursor() as cur:

            # 1. Validar se o diagnóstico pertence à escola,
            # série e turma do estudante.
            cur.execute(
                """
                SELECT dr.id
                FROM diagnostic_requests dr
                INNER JOIN student s
                    ON s.id = %s
                WHERE dr.id = %s
                  AND dr.status = 'aberto'
                  AND (dr.closing_date IS NULL OR dr.closing_date > NOW())
                  AND (dr.opening_date IS NULL OR dr.opening_date <= NOW())
                  AND dr.school_id = s.school_id
                  AND dr.grade = s.grade
                  AND dr.class = s.class;
                """,
                (student_id, order_id)
            )

            validacao = cur.fetchone()

            if not validacao:
                raise ValueError(
                    "Este diagnóstico não está disponível "
                    "para o estudante."
                )

            # 2. Criar ou atualizar cabeçalho de resposta (diagnosis_answer).
            #    Primeiro tentamos o UPDATE para não consumir a sequence
            #    quando o aluno apenas reenvia/atualiza o questionário.
            cur.execute(
                """
                UPDATE diagnosis_answer
                SET send_date = NOW()
                WHERE order_id = %s
                  AND student_id = %s
                RETURNING id;
                """,
                (order_id, student_id)
            )
            row = cur.fetchone()

            if row:
                answer_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO diagnosis_answer (order_id, student_id, send_date)
                    SELECT %s, %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM diagnosis_answer
                        WHERE order_id = %s
                          AND student_id = %s
                    )
                    RETURNING id;
                    """,
                    (order_id, student_id, order_id, student_id)
                )
                row = cur.fetchone()

                if not row:
                    # Outra transação pode ter criado a resposta entre o
                    # UPDATE e o INSERT; recuperamos o registro existente.
                    cur.execute(
                        """
                        SELECT id
                        FROM diagnosis_answer
                        WHERE order_id = %s
                          AND student_id = %s
                        LIMIT 1;
                        """,
                        (order_id, student_id)
                    )
                    row = cur.fetchone()

                if not row:
                    raise ValueError(
                        "Não foi possível registrar a resposta do diagnóstico."
                    )

                answer_id = row[0]

            # 3. Dados socioeconômicos (socioeconomic_data)
            family_income = form_data.get('family_income')
            works = form_data.get('works_besides_studying') == 'sim'
            work_hours = int(form_data.get('work_hours_per_week', 0) or 0) if works else 0
            parents_edu = form_data.get('parents_education')
            has_internet = form_data.get('has_internet_at_home') == 'sim'
            has_computer = form_data.get('has_computer_at_home') == 'sim'

            cur.execute(
                """
                UPDATE socioeconomic_data SET
                    family_income = %s,
                    works_besides_studying = %s,
                    work_hours_per_week = %s,
                    parents_education = %s,
                    has_internet_at_home = %s,
                    has_computer_at_home = %s,
                    updated_at = NOW()
                WHERE answer_id = %s;
                """,
                (family_income, works, work_hours, parents_edu, has_internet, has_computer, answer_id)
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO socioeconomic_data (
                        answer_id, family_income, works_besides_studying, work_hours_per_week,
                        parents_education, has_internet_at_home, has_computer_at_home, updated_at
                    )
                    SELECT %s, %s, %s, %s, %s, %s, %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM socioeconomic_data
                        WHERE answer_id = %s
                    );
                    """,
                    (
                        answer_id,
                        family_income,
                        works,
                        work_hours,
                        parents_edu,
                        has_internet,
                        has_computer,
                        answer_id
                    )
                )

            # 4. Vivência escolar (school_experiences)
            teachers_relations = form_data.get('teachers_relations')
            opinion_heard = form_data.get('opinion_is_heard_at_school') == 'sim'
            learning_diff = form_data.get('learning_difficulties', '')

            cur.execute(
                """
                UPDATE school_experiences SET
                    teachers_relations = %s,
                    opinion_is_heard_at_school = %s,
                    learning_difficulties = %s,
                    updated_at = NOW()
                WHERE answer_id = %s;
                """,
                (teachers_relations, opinion_heard, learning_diff, answer_id)
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO school_experiences (
                        answer_id, teachers_relations, opinion_is_heard_at_school, learning_difficulties, updated_at
                    )
                    SELECT %s, %s, %s, %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM school_experiences
                        WHERE answer_id = %s
                    );
                    """,
                    (
                        answer_id,
                        teachers_relations,
                        opinion_heard,
                        learning_diff,
                        answer_id
                    )
                )

            # 5. Expectativas e sonhos (expectations_dreams)
            goals = form_data.get('personal_professional_goals', '')
            school_support = form_data.get('support_that_the_school_should_offer', '')

            cur.execute(
                """
                UPDATE expectations_dreams SET
                    personal_professional_goals = %s,
                    support_that_the_school_should_offer = %s,
                    updated_at = NOW()
                WHERE answer_id = %s;
                """,
                (goals, school_support, answer_id)
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO expectations_dreams (
                        answer_id, personal_professional_goals, support_that_the_school_should_offer, updated_at
                    )
                    SELECT %s, %s, %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM expectations_dreams
                        WHERE answer_id = %s
                    );
                    """,
                    (answer_id, goals, school_support, answer_id)
                )

            # 6. Contexto cultural (cultural_context)
            cultural_acts = form_data.get('cultural_activities', '')
            comm_trad = form_data.get('community_cultural_tradition', '')
            fam_role = form_data.get('role_family_community_training', '')

            cur.execute(
                """
                UPDATE cultural_context SET
                    cultural_activities = %s,
                    community_cultural_tradition = %s,
                    role_family_community_training = %s,
                    updated_at = NOW()
                WHERE answer_id = %s;
                """,
                (cultural_acts, comm_trad, fam_role, answer_id)
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO cultural_context (
                        answer_id, cultural_activities, community_cultural_tradition, role_family_community_training, updated_at
                    )
                    SELECT %s, %s, %s, %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM cultural_context
                        WHERE answer_id = %s
                    );
                    """,
                    (answer_id, cultural_acts, comm_trad, fam_role, answer_id)
                )

        conn.commit()
        return answer_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def usuario_precisa_atualizar_perfil(user_id):
    """
    Verifica se o usuário precisa completar o perfil após o Primeiro Acesso.

    A conta é considerada pendente enquanto a senha armazenada ainda não for
    um hash bcrypt. Contas ativadas pelo primeiro acesso permanecem com a
    senha temporária em texto puro até que o usuário defina uma senha
    permanente em /perfil/completar.
    """
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT password FROM users WHERE id = %s LIMIT 1;
            """, (user_id,))
            row = cur.fetchone()

            if not row or row[0] is None:
                return True

            stored_password = row[0]

            if isinstance(stored_password, memoryview):
                stored_password = bytes(stored_password)

            if isinstance(stored_password, bytes):
                return not stored_password.startswith(b"$2")

            stored_password = str(stored_password)

            return not stored_password.startswith("$2")
    finally:
        conn.close()


def get_inactive_user_by_identifier(identificador):
    """
    Retorna dados básicos de uma conta inativa encontrada por usuário ou
    e-mail. Usado apenas para orientar o usuário a procurar o Primeiro
    Acesso em vez de receber uma mensagem genérica de credenciais.
    """
    identificador_limpo = (identificador or "").strip().lower()

    if not identificador_limpo:
        return None

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email
                FROM users
                WHERE is_active = FALSE
                  AND (
                    LOWER(email) = %s
                    OR LOWER(username) = %s
                  )
                LIMIT 1;
                """,
                (identificador_limpo, identificador_limpo)
            )
            row = cur.fetchone()

            if not row:
                return None

            return {
                "id": str(row[0]),
                "nome": row[1],
                "email": row[2]
            }
    finally:
        conn.close()


def validar_primeiro_acesso(username, senha):
    """
    Valida o primeiro acesso verificando o código (ou e-mail) e a senha
    temporária de uma conta com is_active = FALSE.

    Retorna (dados_usuario, erro). Em caso de sucesso, erro é None.
    """
    identificador = (username or "").strip().lower()

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, function, password, is_active
                FROM users
                WHERE LOWER(username) = %s OR LOWER(email) = %s
                LIMIT 1;
            """, (identificador, identificador))
            row = cur.fetchone()

            if not row:
                return None, "Código de acesso não encontrado. Confira os dados fornecidos pela instituição."

            user_id, nome, funcao, senha_cadastrada, is_active = row

            if is_active:
                return None, (
                    "Esta conta já foi ativada. Use a opção 'Fazer Login' "
                    "com seu usuário/e-mail e senha."
                )

            # Verifica senha — suporta bcrypt e texto puro (seeds de desenvolvimento)
            senha_valida = False
            if senha_cadastrada:
                try:
                    if isinstance(senha_cadastrada, str):
                        senha_cadastrada_bytes = senha_cadastrada.encode("utf-8")
                    else:
                        senha_cadastrada_bytes = bytes(senha_cadastrada)
                    senha_valida = bcrypt.checkpw(senha.encode("utf-8"), senha_cadastrada_bytes)
                except ValueError:
                    # Fallback para senhas em texto puro (ambiente de desenvolvimento/seed)
                    senha_valida = (senha == senha_cadastrada)

            if not senha_valida:
                return None, "Senha temporária incorreta."

            return {"user_id": user_id, "nome": nome, "funcao": funcao}, None
    finally:
        conn.close()


def ativar_conta_primeiro_acesso(user_id):
    """
    Marca a conta como ativa (is_active = TRUE) após validação do primeiro acesso.
    O usuário é direcionado em seguida para a atualização obrigatória do perfil.
    """
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET is_active = TRUE, updated_at = NOW()
                WHERE id = %s;
            """, (user_id,))
        conn.commit()
        return True, "Conta ativada! Agora defina seus dados de acesso."
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao ativar conta: {str(e)}"
    finally:
        conn.close()


def atualizar_perfil(user_id, novo_username, email, nova_senha):
    """
    Atualiza o perfil do usuário após o primeiro acesso:
    define novo username, e-mail e nova senha (com hash bcrypt).
    Mantém também o e-mail sincronizado nas tabelas student/teachers.
    """
    passwd_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    novo_username = (novo_username or "").strip()
    email = (email or "").strip().lower()

    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            # Verifica se o novo username já está em uso por outro usuário
            cur.execute("""
                SELECT id FROM users
                WHERE LOWER(username) = LOWER(%s) AND id != %s
                LIMIT 1;
            """, (novo_username, user_id))
            if cur.fetchone():
                return False, "Este nome de usuário já está em uso. Escolha outro."

            # Verifica se o novo e-mail já está em uso por outro usuário
            cur.execute("""
                SELECT id FROM users
                WHERE LOWER(email) = %s AND id != %s
                LIMIT 1;
            """, (email, user_id))
            if cur.fetchone():
                return False, "Este e-mail já está em uso. Escolha outro."

            cur.execute("""
                UPDATE users
                SET username = %s, email = %s, password = %s, updated_at = NOW()
                WHERE id = %s;
            """, (novo_username, email, passwd_hash, user_id))

            # Mantém os vínculos de estudante/professor alinhados ao novo e-mail
            cur.execute("""
                UPDATE student SET email = %s WHERE user_id = %s;
            """, (email, user_id))
            cur.execute("""
                UPDATE teachers SET email = %s WHERE user_id = %s;
            """, (email, user_id))
        conn.commit()
        return True, "Perfil atualizado com sucesso!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao atualizar perfil: {str(e)}"
    finally:
        conn.close()


def ativar_conta(user_id, senha, email=None):
    """
    [LEGADO] Ativa o usuário cadastrando sua senha e marcando is_active = TRUE.
    Mantido por compatibilidade; o fluxo atual usa ativar_conta_primeiro_acesso()
    seguido de atualizar_perfil() após o login.
    """
    passwd_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = database.get_connection()
    try:
        with conn.cursor() as cur:
            if email:
                cur.execute("""
                    UPDATE users 
                    SET password = %s, email = %s, is_active = TRUE, updated_at = NOW()
                    WHERE id = %s;
                """, (passwd_hash, email.strip().lower(), user_id))
            else:
                cur.execute("""
                    UPDATE users 
                    SET password = %s, is_active = TRUE, updated_at = NOW()
                    WHERE id = %s;
                """, (passwd_hash, user_id))
        conn.commit()
        return True, "Conta ativada com sucesso! Você já pode entrar com seu usuário ou e-mail e senha."
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao ativar conta: {str(e)}"
    finally:
        conn.close()