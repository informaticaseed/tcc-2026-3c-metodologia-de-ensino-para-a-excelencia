import subprocess
import threading
import uuid
import atexit
import os

env = os.environ.copy()
env["PGOPTIONS"] = "-c search_path=sc_student_diagnosis,public"

psql = subprocess.Popen(
    [
        r"psql",
        "-U", "postgres",
        "-d", "sistema",
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