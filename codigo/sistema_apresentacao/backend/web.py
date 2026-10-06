from flask import Flask, render_template, request, redirect, url_for, flash, session
import auth

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config["SECRET_KEY"] = "tcc-metodologia-ensino-excelencia-secret-key-2026"


def start_server():
    app.run(debug=True, host="127.0.0.1", port=5000)


@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/cadastro', methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        perfil = request.form.get("perfil", "estudante")
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        confirma_senha = request.form.get("confirma_senha", "")

        if not nome or not email or not senha:
            flash("Por favor, preencha todos os campos obrigatórios.", "danger")
            return render_template("cadastro.html", perfil=perfil, nome=nome, email=email)

        if senha != confirma_senha:
            flash("As senhas informadas não coincidem. Tente novamente.", "danger")
            return render_template("cadastro.html", perfil=perfil, nome=nome, email=email)

        try:
            auth.create_account(nome, email, senha, role=perfil)
            flash("Conta criada com sucesso! Faça seu login para acessar o sistema.", "success")
            return redirect(url_for('login', identificador=email))
        except auth.UserAlreadyExistsError:
            flash("Já existe uma conta cadastrada com este e-mail!", "danger")
            return render_template("cadastro.html", perfil=perfil, nome=nome, email=email)
        except Exception as e:
            flash(f"Erro ao criar conta no banco de dados: {str(e)}", "danger")
            return render_template("cadastro.html", perfil=perfil, nome=nome, email=email)

    return render_template("cadastro.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('identificador', '').strip()
        password = request.form.get('senha', '')

        if not email or not password:
            flash('Preencha o e-mail e a senha de acesso.', 'danger')
            return render_template('login.html', identificador=email)

        user_uuid = auth.get_user_uuid(email)
        user = auth.authenticate_user(user_uuid, password) if user_uuid else None

        if user is None:
            flash('Credenciais incorretas. Verifique seu e-mail e senha.', 'danger')
            return render_template('login.html', identificador=email)

        session.clear()
        session['user_id'] = user['id']
        session['user_nome'] = user['nome']
        session['user_email'] = user['email']
        session['user_perfil'] = user['perfil']

        flash(f"Bem-vindo(a), {user['nome']}! Acesso concedido.", 'success')
        return redirect(url_for('dashboard'))

    identificador = request.args.get('identificador', '')
    return render_template('login.html', identificador=identificador)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar esta página.", "warning")
        return redirect(url_for('login'))

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    # Estatísticas reais do banco de dados
    stats = auth.get_users_statistics()
    lista_usuarios = auth.get_all_users() if usuario['perfil'] == 'admin' else []

    # Metodologias didáticas ativas cadastradas no escopo do TCC
    metodologias = [
        {
            'titulo': 'Aprendizagem Baseada em Problemas (PBL)',
            'categoria': 'Colaborativa / Investigativa',
            'descricao': 'Os estudantes são desafiados a solucionar problemas complexos do mundo real de forma interdisciplinar.',
            'icone': 'bi-lightbulb-fill',
            'cor': 'primary'
        },
        {
            'titulo': 'Sala de Aula Invertida (Flipped Classroom)',
            'categoria': 'Autonomia / Pré-Aula',
            'descricao': 'O contato inicial com os conteúdos teóricos ocorre antes da aula presencial, otimizando o tempo em grupo.',
            'icone': 'bi-arrow-repeat',
            'cor': 'success'
        },
        {
            'titulo': 'Gamificação Pedagógica',
            'categoria': 'Engajamento / Motivação',
            'descricao': 'Mecânicas e dinâmicas de jogos aplicadas ao processo de ensino para impulsionar a participação estudantil.',
            'icone': 'bi-controller',
            'cor': 'warning'
        },
        {
            'titulo': 'Instrução por Pares (Peer Instruction)',
            'categoria': 'Debate / Argumentação',
            'descricao': 'Técnica desenvolvida em Harvard que utiliza perguntas conceituais e discussões em pequenos grupos de alunos.',
            'icone': 'bi-people-fill',
            'cor': 'info'
        },
        {
            'titulo': 'Design Thinking na Educação',
            'categoria': 'Criatividade / Empatia',
            'descricao': 'Abordagem centrada no ser humano para prototipagem e solução criativa de desafios da comunidade escolar.',
            'icone': 'bi-palette-fill',
            'cor': 'purple'
        }
    ]

    return render_template(
        'dashboard.html',
        usuario=usuario,
        total_usuarios=stats['total_usuarios'],
        total_professores=stats['total_professores'],
        total_estudantes=stats['total_estudantes'],
        lista_usuarios=lista_usuarios,
        metodologias=metodologias
    )


@app.route('/resultados')
def resultados():
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar os resultados analíticos.", "warning")
        return redirect(url_for('login'))

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    summary = auth.get_student_analytics_summary()

    return render_template(
        'resultados.html',
        usuario=usuario,
        summary=summary
    )


@app.route('/questionario', methods=['GET', 'POST'])
def questionario():
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar o questionário.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    aluno = auth.get_student_by_user_id(user_id)

    # Se a conta não for de aluno (ex: professor logado), busca/cria uma referência para teste
    if not aluno:
        flash("Você precisa estar conectado como estudante para responder ao questionário.", "info")
        return redirect(url_for('dashboard'))

    pedido = auth.get_available_diagnostic_request(aluno['id'])
    if not pedido:
        flash("Não há pedidos de diagnóstico abertos no momento.", "info")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            order_id = int(request.form.get('order_id', pedido['id']))
            auth.save_questionnaire_response(aluno['id'], order_id, request.form)
            flash("Suas respostas foram salvas com sucesso no banco de dados! Muito obrigado pela participação.", "success")
            return redirect(url_for('questionario'))
        except Exception as e:
            flash(f"Ocorreu um erro ao salvar o questionário: {str(e)}", "danger")

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    return render_template(
        'questionario.html',
        usuario=usuario,
        aluno=aluno,
        pedido=pedido
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    start_server()