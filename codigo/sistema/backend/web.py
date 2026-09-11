from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import auth
import database
import tools

app = Flask(__name__, template_folder="../templates", static_folder="../static")

def start_server():
    app.run(debug=True, host="0.0.0.0")

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/cadastro')
def cadastro():
        return render_template("cadastro.html")

@app.route('/dashboard')
def dashboard():
        return render_template("dashboard.html")

@app.route('/login')
def login():
        return render_template("login.html")

@app.route("/db")
def db_terminal():
    return render_template("db_terminal.html")

@app.route("/db/execute", methods=["POST"])
def db_execute():

    command = request.get_data(as_text=True)

    try:
        return tools.execute_psql(command)

    except Exception as e:
        return str(e), 500