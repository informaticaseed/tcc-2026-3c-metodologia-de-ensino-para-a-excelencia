import subprocess
import threading
import uuid
import atexit
import os

import shutil

# Localiza o psql no PATH ou usa o caminho padrão do PostgreSQL 18 no Windows
PSQL_BIN = shutil.which("psql") or r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

env = os.environ.copy()
env["PGOPTIONS"] = "-c search_path=sc_student_diagnosis,public"
env["PGPASSWORD"] = os.getenv("DB_PASSWORD", "1234")

psql = subprocess.Popen(
    [
        PSQL_BIN,
        "-h", os.getenv("DB_HOST", "127.0.0.1"),
        "-p", os.getenv("DB_PORT", "5432"),
        "-U", os.getenv("DB_USER", "postgres"),
        "-d", os.getenv("DB_NAME", "sistema"),
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env=env
)

psql_lock = threading.Lock()


def execute_psql(command):

    marker = f"__FLASK_END_{uuid.uuid4().hex}__"

    with psql_lock:

        psql.stdin.write(command + "\n")
        psql.stdin.write(f"\\echo {marker}\n")
        psql.stdin.flush()

        output = []

        for line in psql.stdout:

            if line.rstrip("\r\n") == marker:
                break

            output.append(line)

    return "".join(output)


@atexit.register
def close_psql():

    if psql.poll() is None:
        psql.terminate()
        psql.wait()