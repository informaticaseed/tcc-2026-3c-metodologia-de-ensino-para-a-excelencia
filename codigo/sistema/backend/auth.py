import database
import bcrypt

def get_user_uuid(username):
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id
            FROM sc_diagnostico_estudantil.usuarios
            WHERE nome_usuario   = %s;
            """,
            (username,)
        )

        uuid = cursor.fetchone()

        if uuid is None:
            return None

        return uuid[0]

def create_account(username, email, password):
    if (get_user_uuid(username) is not None):
        raise UserAlreadyExistsError("User already exists")
    
    passwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")  #Encripta a senha.

    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sc_diagnostico_estudantil.usuarios (nome_usuario, email, senha, papel)
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
            DELETE FROM sc_diagnostico_estudantil.usuarios
            WHERE id = %s;
            """,
            (uuid,)
        )

def login(uuid, password):
    with database.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT senha
                FROM sc_diagnostico_estudantil.usuarios
                WHERE id = %s
                """,
                (uuid,)
            )
            result = cursor.fetchone()
    if result is None:
        return False
    passwrd_hash = result[0]
    match = bcrypt.checkpw(password.encode("utf-8"), passwrd_hash.encode("utf-8"))
    return match

class UserAlreadyExistsError(Exception):
    pass
