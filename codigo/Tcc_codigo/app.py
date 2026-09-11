import os
import re
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-secreta-plataforma-educacional-2026')
DATABASE = os.path.join(app.root_path, 'plataforma_educacional.db')

# --- BANCO DE DADOS (SQLite) ---

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Inicializa as tabelas do banco de dados e cria usuários de demonstração se estiver vazio."""
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                cpf TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK(perfil IN ('admin', 'professor', 'estudante')),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

        # Seed de contas de demonstração caso o banco seja recém-criado
        cursor = db.execute('SELECT COUNT(*) as count FROM usuarios')
        if cursor.fetchone()['count'] == 0:
            demo_users = [
                ('Administrador Geral', 'admin@metodologias.com', '111.222.333-44', 'admin123', 'admin'),
                ('Prof. Dr. Carlos Eduardo', 'carlos.professor@metodologias.com', '222.333.444-55', 'prof123', 'professor'),
                ('Mariana Silva (Aluna)', 'mariana.estudante@metodologias.com', '333.444.555-66', 'aluno123', 'estudante'),
            ]
            for nome, email, cpf, senha, perfil in demo_users:
                cpf_limpo = limpar_cpf(cpf)
                senha_hash = generate_password_hash(senha)
                db.execute(
                    'INSERT INTO usuarios (nome, email, cpf, senha_hash, perfil) VALUES (?, ?, ?, ?, ?)',
                    (nome, email.lower().strip(), cpf_limpo, senha_hash, perfil)
                )
            db.commit()

# --- UTILITÁRIOS E VALIDAÇÕES ---

def limpar_cpf(cpf_str):
    """Remove pontuação e caracteres não numéricos do CPF."""
    return re.sub(r'\D', '', cpf_str or '')

def formatar_cpf(cpf_limpo):
    """Formata CPF no formato 000.000.000-00."""
    cpf_limpo = limpar_cpf(cpf_limpo)
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf_limpo

def validar_cpf(cpf_str):
    """Valida o formato e os dígitos verificadores do CPF."""
    cpf = limpar_cpf(cpf_str)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Cálculo do 1º dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if int(cpf[9]) != digito1:
        return False
    
    # Cálculo do 2º dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    if int(cpf[10]) != digito2:
        return False
        
    return True

def validar_email(email_str):
    """Valida a estrutura do e-mail."""
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(padrao, email_str or '') is not None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Context processor para disponibilizar dados úteis nos templates
@app.context_processor
def inject_global_data():
    return {
        'formatar_cpf': formatar_cpf,
        'ano_atual': 2026,
        'app_name': 'EduMetodologias'
    }

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf_bruto = request.form.get('cpf', '').strip()
        perfil = request.form.get('perfil', '').strip().lower()
        senha = request.form.get('senha', '')
        confirma_senha = request.form.get('confirma_senha', '')

        cpf_limpo = limpar_cpf(cpf_bruto)

        # Validações
        erros = []
        if not nome or len(nome) < 3:
            erros.append('Informe seu nome completo (mínimo 3 caracteres).')
        
        if not validar_email(email):
            erros.append('Informe um endereço de e-mail válido.')

        if not validar_cpf(cpf_limpo):
            erros.append('O CPF informado é inválido.')

        if perfil not in ['admin', 'professor', 'estudante']:
            erros.append('Selecione um tipo de perfil válido (Administrador, Professor ou Estudante).')

        if len(senha) < 6:
            erros.append('A senha deve ter no mínimo 6 caracteres.')

        if senha != confirma_senha:
            erros.append('As senhas não coincidem.')

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('cadastro.html', nome=nome, email=email, cpf=cpf_bruto, perfil=perfil)

        db = get_db()

        # Verificar duplicidade de E-mail
        usuario_existente_email = db.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
        if usuario_existente_email:
            flash('Este e-mail já está cadastrado no sistema.', 'danger')
            return render_template('cadastro.html', nome=nome, email=email, cpf=cpf_bruto, perfil=perfil)

        # Verificar duplicidade de CPF
        usuario_existente_cpf = db.execute('SELECT id FROM usuarios WHERE cpf = ?', (cpf_limpo,)).fetchone()
        if usuario_existente_cpf:
            flash('Este CPF já está cadastrado no sistema.', 'danger')
            return render_template('cadastro.html', nome=nome, email=email, cpf=cpf_bruto, perfil=perfil)

        # Inserir no Banco de Dados
        senha_hash = generate_password_hash(senha)
        db.execute(
            'INSERT INTO usuarios (nome, email, cpf, senha_hash, perfil) VALUES (?, ?, ?, ?, ?)',
            (nome, email, cpf_limpo, senha_hash, perfil)
        )
        db.commit()

        flash('Cadastro realizado com sucesso! Agora você já pode fazer login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        senha = request.form.get('senha', '')
        perfil_esperado = request.form.get('perfil', '').strip().lower()

        if not identificador or not senha:
            flash('Preencha o identificador (E-mail ou CPF) e a senha.', 'danger')
            return render_template('login.html', identificador=identificador, perfil=perfil_esperado)

        db = get_db()
        id_limpo_cpf = limpar_cpf(identificador)

        # Busca por e-mail ou por CPF
        usuario = db.execute(
            'SELECT * FROM usuarios WHERE email = ? OR cpf = ?',
            (identificador.lower(), id_limpo_cpf)
        ).fetchone()

        if not usuario or not check_password_hash(usuario['senha_hash'], senha):
            flash('Credenciais incorretas. Verifique seu e-mail/CPF e senha.', 'danger')
            return render_template('login.html', identificador=identificador, perfil=perfil_esperado)

        # Se o usuário filtrou por um perfil específico na tela de login e divergiu
        if perfil_esperado and perfil_esperado != usuario['perfil']:
            flash(f"Esta conta possui o perfil '{usuario['perfil'].capitalize()}', mas você tentou entrar como '{perfil_esperado.capitalize()}'.", 'warning')
            return render_template('login.html', identificador=identificador, perfil=perfil_esperado)

        # Iniciar sessão
        session.clear()
        session['user_id'] = usuario['id']
        session['user_nome'] = usuario['nome']
        session['user_email'] = usuario['email']
        session['user_cpf'] = usuario['cpf']
        session['user_perfil'] = usuario['perfil']

        flash(f"Bem-vindo(a), {usuario['nome']}! Acesso concedido como {usuario['perfil'].capitalize()}.", 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    
    # Obter dados atualizados do usuário logado
    usuario = db.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    if not usuario:
        session.clear()
        flash('Usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('login'))

    # Estatísticas de demonstração para a plataforma educacional
    total_usuarios = db.execute('SELECT COUNT(*) as count FROM usuarios').fetchone()['count']
    total_professores = db.execute("SELECT COUNT(*) as count FROM usuarios WHERE perfil = 'professor'").fetchone()['count']
    total_estudantes = db.execute("SELECT COUNT(*) as count FROM usuarios WHERE perfil = 'estudante'").fetchone()['count']

    # Metodologias cadastradas na plataforma
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

    # Lista de todos os usuários (visível apenas para admin)
    lista_usuarios = []
    if usuario['perfil'] == 'admin':
        lista_usuarios = db.execute('SELECT id, nome, email, cpf, perfil, criado_em FROM usuarios ORDER BY id DESC').fetchall()

    return render_template(
        'dashboard.html',
        usuario=usuario,
        total_usuarios=total_usuarios,
        total_professores=total_professores,
        total_estudantes=total_estudantes,
        metodologias=metodologias,
        lista_usuarios=lista_usuarios
    )

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    print("===================================================================")
    print(" Plataforma Educacional de Metodologias Eficazes - Servidor Ativo")
    print(" Acesse em: http://127.0.0.1:5000")
    print(" Contas demo disponíveis:")
    print("  - Admin:     admin@metodologias.com / admin123")
    print("  - Professor: carlos.professor@metodologias.com / prof123")
    print("  - Estudante: mariana.estudante@metodologias.com / aluno123")
    print("===================================================================")
    app.run(debug=True, port=5000)

