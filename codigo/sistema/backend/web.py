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
        senha = request.form.get("senha")

        try:
            auth.create_account(nome, email, senha)
        except auth.UserAlreadyExistsError:
             flash("Esse usuário já existe!", "danger")

        return redirect(url_for('login'))


    return render_template("cadastro.html")

@app.route('/dashboard')
def dashboard():

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil']
    }

    metodologias = [
            {
                'titulo': 'Aprendizagem Baseada em Problemas (PBL)',
                'categoria': 'Colaborativa / Investigativa',
                'descricao': 'Os alunos aprendem os temas curriculares ao resolver problemas do mundo real em equipes.',
                'icone': 'bi-puzzle',
                'cor': 'primary'
            },
            {
                'titulo': 'Sala de Aula Invertida (Flipped Classroom)',
                'categoria': 'Autonomia / Pré-aula',
                'descricao': 'O conteúdo teórico é absorvido previamente em casa e a sala de aula torna-se espaço de debate prático.',
                'icone': 'bi-arrow-repeat',
                'cor': 'success'
            },
            {
                'titulo': 'Gamificação no Ensino',
                'categoria': 'Engajamento e Recompensas',
                'descricao': 'Uso de mecânicas de jogos (pontos, fases, desafios) para potencializar a retenção e o foco.',
                'icone': 'bi-controller',
                'cor': 'warning'
            },
            {
                'titulo': 'Instrução por Pares (Peer Instruction)',
                'categoria': 'Interação / Feedback',
                'descricao': 'Debates estruturados entre os próprios estudantes para consolidação de conceitos críticos.',
                'icone': 'bi-people',
                'cor': 'info'
            },
            {
                'titulo': 'Design Thinking na Educação',
                'categoria': 'Criatividade / Empatia',
                'descricao': 'Processo centrado no ser humano para criação de soluções pedagógicas inovadoras.',
                'icone': 'bi-lightbulb',
                'cor': 'danger'
            },
            {
                'titulo': 'Microlearning e Pílulas de Conteúdo',
                'categoria': 'Agilidade / Retenção',
                'descricao': 'Aulas curtas, focadas e dinâmicas para fixação rápida com recursos multimídia.',
                'icone': 'bi-phone',
                'cor': 'secondary'
            }
        ]

    return render_template(
            'dashboard.html',
            usuario=usuario,
            total_usuarios=9999,
            total_professores=99,
            total_estudantes=99,
            metodologias=metodologias,
        )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('identificador', '').strip()
        password = request.form.get('senha', '')

        if not email or not password:
            flash('Preencha o E-mail e a senha.', 'danger')
            return render_template('login.html', identificador=email)

        user = auth.authenticate_user(auth.get_user_uuid(email), password)

        if user is None:
                    flash(f'Credenciais incorretas. Verifique seu e-mail e senha.', 'danger')
                    return render_template('login.html', identificador=email)

        
        session.clear()
        session['user_id'] = user['id']
        session['user_nome'] = user['nome']
        session['user_email'] = user['email']
        session['user_perfil'] = user['perfil']
        
        flash(f"Bem-vindo(a), {email}! Acesso concedido.", 'success')
        return redirect(url_for('dashboard')) 
         
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('login'))





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