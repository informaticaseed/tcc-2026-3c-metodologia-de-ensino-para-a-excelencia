import database
import bcrypt

def get_user_uuid(email):
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email   = %s;
            """,
            (email,)
        )

        uuid = cursor.fetchone()

        if uuid is None:
            return None

        return uuid[0]

def create_account(username, email, password):
    if (get_user_uuid(email) is not None):
        raise UserAlreadyExistsError("User already exists")
    
    passwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")  #Encripta a senha.

    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (name_user, email, password, function)
            VALUES (%s, %s, %s, 'aluno');
            """,
            (username.strip().upper(), email, passwd_hash,)
        )

def get_user_by_username(username):  #ALTO RISCO DE SEGURANÇA, APAGAR NO FUTURO
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM sc_diagnostico_estudantil.usuarios
            WHERE nome_usuario = %s
            """,
            (username,)
        )

        return cursor.fetchone()

def delete_account(uuid):

    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM users
            WHERE id = %s;
            """,
            (uuid,)
        )

def authenticate_user(uuid, password):
    with database.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name_user, email, function, password
                FROM users
                WHERE id = %s
                """,
                (uuid,)
            )
            result = cursor.fetchone()
    if result is None:
        return None

    user_id, name, user_email, role, passwrd_hash = result

    if not bcrypt.checkpw(password.encode("utf-8"), passwrd_hash.encode("utf-8")):
        return None

    return {
        "id": user_id,
        "nome": name,
        "email": user_email,
        "perfil": role
    }

class UserAlreadyExistsError(Exception):
    pass
