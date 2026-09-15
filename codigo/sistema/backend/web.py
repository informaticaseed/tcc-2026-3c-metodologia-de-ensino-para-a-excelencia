from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import auth
import database
import tools

app = Flask(__name__, template_folder="../templates", static_folder="../static")

app.config["SECRET_KEY"] = "change-this-to-a-random-secret"

def start_server():
    app.run(debug=True, host="0.0.0.0")

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/cadastro', methods=["POST", "GET"])
def cadastro():

    if request.method == "POST":
        perfil = request.form.get("perfil")
        nome = request.form.get("nome")
        email = request.form.get("email")
        cpf = request.form.get("cpf")
        senha = request.form.get("senha")

        try:
            auth.create_account(nome, email, senha)
        except auth.UserAlreadyExistsError:
             flash("Esse usuário já existe!", "danger")


    return render_template("cadastro.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        password = request.form.get('senha', '')

        if not identificador or not password:
            flash('Preencha o identificador (E-mail ou CPF) e a senha.', 'danger')
            return render_template('login.html', identificador=identificador)

        if not auth.login(auth.get_user_uuid(identificador.upper()), password):
                    flash('Credenciais incorretas. Verifique seu e-mail/CPF e senha.', 'danger')
                    return render_template('login.html', identificador=identificador)
        
        flash(f"Bem-vindo(a), {identificador}! Acesso concedido.", 'success')
        return redirect(url_for('dashboard')) 
         
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