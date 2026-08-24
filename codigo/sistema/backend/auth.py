import database
import bcrypt

def user_exists(username):
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT 1
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        return cursor.fetchone() is not None

def create_account(username, password):
    if (user_exists(username)):
        raise UserAlreadyExistsError("User already exists")
    
    passwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())  #Encripta a senha.

    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, 'user');
            """,
            (username, passwd_hash,)
        )

def get_user_by_username(username):
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = %s
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

def login(username, password):
    user_hash = get_user_by_username(username)[2]
    match = bcrypt.checkpw(password.encode("utf-8"), user_hash)
    return match

class UserAlreadyExistsError(Exception):
    pass
