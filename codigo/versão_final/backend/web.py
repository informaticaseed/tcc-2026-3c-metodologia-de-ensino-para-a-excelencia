import os
import sys
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    abort
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ANALYTICS_DIR = os.path.join(BASE_DIR, "analise_de_dados")

if ANALYTICS_DIR not in sys.path:
    sys.path.insert(0, ANALYTICS_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import academico
import auth
import tools
import relatorio_pedido

app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static")
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "tcc-metodologia-ensino-excelencia-secret-key-2026")

# Versões dos documentos legais exibidas nas páginas e no cadastro.
# Incremente ao alterar o conteúdo jurídico.
TERMOS_VERSAO = "1.0"
POLITICA_VERSAO = "1.0"
TERMOS_VIGENCIA = "02 de novembro de 2026"
POLITICA_VIGENCIA = "06 de novembro de 2026"
LGPD_CONTATO = os.getenv(
    "LGPD_CONTATO_EMAIL",
    "privacidade@edumetodologias.com.br"
)
LGPD_ENCARREGADO = os.getenv(
    "LGPD_ENCARREGADO_NOME",
    "Encarregado de Proteção de Dados da instituição de ensino"
)


@app.context_processor
def _injetar_contexto_global():
    """Disponibiliza séries, turmas, ano e dados dos documentos legais."""
    return {
        "series_ensino_medio": academico.SERIES_ENSINO_MEDIO,
        "turmas": academico.TURMAS,
        "ano_atual": datetime.now().year,
        "termos_versao": TERMOS_VERSAO,
        "politica_versao": POLITICA_VERSAO,
        "termos_vigencia": TERMOS_VIGENCIA,
        "politica_vigencia": POLITICA_VIGENCIA,
        "lgpd_contato": LGPD_CONTATO,
        "lgpd_encarregado": LGPD_ENCARREGADO,
    }


@app.route("/termos-de-uso")
def termos_uso():
    """Página pública dos Termos de Uso."""
    return render_template("termos_uso.html")


@app.route("/politica-de-privacidade")
def politica_privacidade():
    """Página pública da Política de Privacidade."""
    return render_template("politica_privacidade.html")


@app.before_request
def _sincronizar_prazos_diagnosticos():
    """
    Encerra automaticamente os pedidos cuja data de encerramento já
    passou, antes de tratar qualquer requisição da aplicação.
    """
    if request.endpoint == 'static':
        return

    try:
        auth.sincronizar_pedidos_vencidos()
    except Exception:
        app.logger.exception(
            "Falha ao sincronizar pedidos de diagnóstico vencidos."
        )


@app.before_request
def _exigir_completar_perfil():
    """
    Impede o acesso ao restante da plataforma enquanto o usuário não
    concluir a atualização obrigatória de perfil.
    """
    if request.endpoint in (
        'static',
        'logout',
        'completar_perfil',
        'termos_uso',
        'politica_privacidade',
    ):
        return

    if session.get('user_id') and session.get('needs_profile_update'):
        flash(
            "Complete seu perfil para continuar utilizando a plataforma.",
            "warning"
        )
        return redirect(url_for('completar_perfil'))


def start_server():
    app.run(debug=True, host="0.0.0.0", port=5000)


@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """
    Tela de Primeiro Acesso / Ativação de Conta.

    O usuário insere o código de acesso (username pré-registrado) e a
    senha temporária pré-definida pela instituição. Caso as credenciais
    sejam válidas e a conta esteja inativa (is_active = FALSE), ela é
    ativada, o usuário é autenticado e redirecionado para completar o perfil.
    Exceção: contas de Admin já estão ativas e não usam este fluxo.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        codigo_acesso = request.form.get('codigo_acesso', '').strip()
        senha_temp    = request.form.get('senha_temporaria', '')

        if not codigo_acesso or not senha_temp:
            flash("Preencha o código de acesso e a senha temporária.", "danger")
            return render_template("cadastro.html", codigo_acesso=codigo_acesso)

        dados, erro = auth.validar_primeiro_acesso(codigo_acesso, senha_temp)
        if erro:
            flash(erro, "danger")
            return render_template("cadastro.html", codigo_acesso=codigo_acesso)

        # Exige a confirmação dos Termos de Uso e da Política de Privacidade
        # antes de ativar a conta. O aceite não é armazenado no banco.
        if request.form.get('aceite_termos') != 'sim':
            flash(
                "Para continuar, leia e aceite os Termos de Uso.",
                "danger"
            )
            return render_template("cadastro.html", codigo_acesso=codigo_acesso)

        if request.form.get('ciencia_privacidade') != 'sim':
            flash(
                "Para continuar, declare que leu e compreendeu a "
                "Política de Privacidade.",
                "danger"
            )
            return render_template("cadastro.html", codigo_acesso=codigo_acesso)

        # Conta localizada e validada — ativar e autenticar o usuário
        sucesso, msg = auth.ativar_conta_primeiro_acesso(dados['user_id'])
        if sucesso:
            usuario = auth.get_user_by_id(dados['user_id'])

            if not usuario:
                flash(
                    "Conta ativada, mas não foi possível carregar seus dados. "
                    "Faça login para continuar.",
                    "warning"
                )
                return redirect(url_for('login'))

            # Mantém o usuário autenticado para concluir o perfil logo após
            # a ativação, sem exigir um novo login.
            session.clear()
            session['user_id'] = usuario['id']
            session['user_nome'] = usuario['username']
            session['user_email'] = usuario['email']
            session['user_perfil'] = usuario['perfil']
            session['needs_profile_update'] = True

            flash(
                "✅ Conta ativada com sucesso! "
                "Agora defina seu nome de usuário, e-mail e senha definitivos.",
                "success"
            )
            return redirect(url_for('completar_perfil'))
        else:
            flash(msg, "danger")

    return render_template("cadastro.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('identificador', '').strip()
        password = request.form.get('senha', '')

        if not email or not password:
            flash('Preencha o usuário ou e-mail e a senha de acesso.', 'danger')
            return render_template('login.html', identificador=email)

        user_uuid = auth.get_user_uuid(email)
        user = auth.authenticate_user(user_uuid, password) if user_uuid else None

        if user is None:
            conta_inativa = auth.get_inactive_user_by_identifier(email)

            if conta_inativa:
                flash(
                    "Sua conta ainda não foi ativada. Use a opção "
                    "'Primeiro Acesso / Ativar Conta' com o código e a "
                    "senha temporária fornecidos pela instituição.",
                    "warning"
                )
            else:
                flash(
                    'Credenciais incorretas. Verifique seu usuário ou '
                    'e-mail e senha.',
                    'danger'
                )

            return render_template('login.html', identificador=email)

        session.clear()
        session['user_id'] = user['id']
        session['user_nome'] = user['nome']
        session['user_email'] = user['email']
        session['user_perfil'] = user['perfil']

        # Detecta se o usuário acabou de fazer o Primeiro Acesso e precisa atualizar o perfil.
        # Um indicador seguro é: o e-mail ainda pertence ao domínio institucional padrão
        # E o username ainda é o código original (sem "@" ou espaços — tratado como código bruto).
        # A forma mais robusta é verificar diretamente no banco se o campo `updated_at` ainda é NULL.
        needs_update = auth.usuario_precisa_atualizar_perfil(user['id'])
        if needs_update:
            session['needs_profile_update'] = True

        flash(f"Bem-vindo(a), {user['nome']}! Acesso concedido.", 'success')

        if needs_update:
            flash("⚠️ Por segurança, atualize seu nome de usuário, e-mail e senha antes de continuar.", "warning")
            return redirect(url_for('completar_perfil'))

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
    if usuario['perfil'] in ('admin', 'superadmin'):
        stats = auth.get_dashboard_statistics(usuario['id'])
        lista_usuarios = auth.get_users_for_actor(usuario['id'])
        contexto_admin = auth.get_user_by_id(usuario['id'])
    else:
        stats = {
            'total_usuarios': 0,
            'total_admins': 0,
            'total_professores': 0,
            'total_estudantes': 0,
            'total_escolas': 0
        }
        lista_usuarios = []
        contexto_admin = None

    # Indicadores do estudante: diagnósticos da turma e respostas enviadas
    diagnosticos_disponiveis = 0
    respostas_enviadas = 0

    if usuario['perfil'] in ('aluno', 'estudante'):
        aluno = auth.get_student_by_user_id(usuario['id'])

        if aluno:
            diagnosticos_disponiveis = len(
                auth.get_available_diagnostic_requests(aluno['id'])
            )
            respostas_enviadas = len(
                auth.get_student_answers(aluno['id'])
            )

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
        total_admins=stats['total_admins'],
        total_professores=stats['total_professores'],
        total_estudantes=stats['total_estudantes'],
        total_escolas=stats['total_escolas'],
        lista_usuarios=lista_usuarios,
        contexto_admin=contexto_admin,
        metodologias=metodologias,
        diagnosticos_disponiveis=diagnosticos_disponiveis,
        respostas_enviadas=respostas_enviadas
    )


@app.route('/admin/usuarios', methods=['GET', 'POST'])
def admin_usuarios():
    """
    Gestão de usuários conforme o nível de acesso.

    - Superadmin cadastra administradores e escolhe a instituição;
    - Admin cadastra professores e estudantes da própria escola.
    """
    if 'user_id' not in session:
        flash(
            "Por favor, faça login para acessar a gestão de usuários.",
            "warning"
        )
        return redirect(url_for('login'))

    perfil = session.get('user_perfil')

    if perfil not in ('admin', 'superadmin'):
        flash("Acesso restrito aos administradores.", "warning")
        return redirect(url_for('dashboard'))

    ator = auth.get_user_by_id(session['user_id'])

    if not ator:
        session.clear()
        flash("Sessão expirada. Faça login novamente.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            resultado = auth.create_managed_user(
                actor_user_id=session['user_id'],
                role=request.form.get('role'),
                full_name=request.form.get('full_name'),
                email=request.form.get('email'),
                username=request.form.get('username'),
                password=request.form.get('password'),
                school_id=request.form.get('school_id'),
                grade=request.form.get('grade'),
                school_class=request.form.get('class')
            )

            if resultado['ativo']:
                flash(
                    "Administrador cadastrado com sucesso! "
                    f"Código de acesso: {resultado['username']}. "
                    "A conta já está ativa e vinculada à instituição.",
                    "success"
                )
            else:
                flash(
                    "Conta cadastrada com sucesso! "
                    f"Código de acesso: {resultado['username']}. "
                    "O usuário deve ativar a conta em 'Primeiro Acesso' "
                    "usando a senha temporária informada.",
                    "success"
                )
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(
                f"Não foi possível cadastrar a conta: {e}",
                "danger"
            )

        return redirect(url_for('admin_usuarios'))

    escolas = auth.get_all_schools() if perfil == 'superadmin' else []
    usuarios = auth.get_users_for_actor(session['user_id'])

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    return render_template(
        'admin_usuarios.html',
        usuario=usuario,
        perfil=perfil,
        ator=ator,
        escolas=escolas,
        usuarios=usuarios
    )


@app.route('/admin/escolas', methods=['GET', 'POST'])
def admin_escolas():
    """Cadastro de instituições de ensino, exclusivo do superadmin."""
    if 'user_id' not in session:
        flash(
            "Por favor, faça login para acessar as instituições.",
            "warning"
        )
        return redirect(url_for('login'))

    if session.get('user_perfil') != 'superadmin':
        flash(
            "Acesso restrito ao superadministrador.",
            "warning"
        )
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            auth.create_school(
                request.form.get('name'),
                request.form.get('inep_code')
            )
            flash(
                "Instituição de ensino cadastrada com sucesso!",
                "success"
            )
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(
                f"Não foi possível cadastrar a instituição: {e}",
                "danger"
            )

        return redirect(url_for('admin_escolas'))

    escolas = auth.get_all_schools()

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    return render_template(
        'admin_escolas.html',
        usuario=usuario,
        escolas=escolas
    )


def _usuario_sessao():
    """Dados básicos do usuário autenticado para os templates."""
    return {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }


def _pedido_do_professor(order_id):
    """Valida login, perfil e propriedade do pedido de diagnóstico."""
    if 'user_id' not in session:
        return None

    if session.get('user_perfil') != 'professor':
        return None

    return auth.get_teacher_diagnostic_request(
        session['user_id'],
        order_id
    )


@app.route('/resultados')
def resultados():
    if 'user_id' not in session:
        flash(
            "Por favor, faça login para acessar os resultados analíticos.",
            "warning"
        )
        return redirect(url_for('login'))

    # Somente professores podem acessar esta página.
    if session.get('user_perfil') != 'professor':
        flash("Acesso restrito aos professores.", "warning")
        return redirect(url_for('dashboard'))

    professor = auth.get_teacher_by_user_id(session['user_id'])

    if not professor:
        flash(
            "Perfil de professor não encontrado para este usuário.",
            "danger"
        )
        return redirect(url_for('dashboard'))

    # Todos os pedidos do professor alimentam o seletor da página.
    pedidos = auth.get_teacher_diagnostic_requests(professor['id'])

    pedido = None
    pedido_solicitado = (request.args.get('pedido_id') or '').strip()

    if pedido_solicitado:
        try:
            pedido_id = int(pedido_solicitado)
        except (TypeError, ValueError):
            pedido_id = None

        if pedido_id is not None:
            pedido = next(
                (p for p in pedidos if p['id'] == pedido_id),
                None
            )

            if pedido is None:
                flash(
                    "Pedido de diagnóstico não encontrado ou não "
                    "vinculado a você.",
                    "warning"
                )

    # Sem seleção explícita, abre o pedido mais recente (lista já ordenada).
    if pedido is None and pedidos:
        pedido = pedidos[0]

    summary = relatorio_pedido.empty_summary()
    relatorios = {}
    relatorios_erro = None

    if pedido:
        try:
            resultado = relatorio_pedido.generate_order_reports(
                pedido['id']
            )

            if resultado.get('available'):
                summary = resultado['summary']

                relatorios = {
                    'pca': url_for(
                        'relatorio_pedido_imagem',
                        order_id=pedido['id'],
                        image_name='pca'
                    ),
                    'dimensoes': url_for(
                        'relatorio_pedido_imagem',
                        order_id=pedido['id'],
                        image_name='dimensoes'
                    ),
                    'turma': url_for(
                        'relatorio_pedido_imagem',
                        order_id=pedido['id'],
                        image_name='turma'
                    ),
                    'nuvens': url_for(
                        'relatorio_pedido_imagem',
                        order_id=pedido['id'],
                        image_name='nuvens'
                    )
                }
            else:
                relatorios_erro = resultado.get('reason')

                # Fallback defensivo: se houver análise global para o
                # pedido, exibe a tabela mesmo sem gerar os gráficos.
                summary = auth.get_student_analytics_summary(
                    session['user_id'],
                    pedido['id']
                )

        except Exception as exc:
            relatorios_erro = (
                "Não foi possível gerar os relatórios deste pedido. "
                f"Detalhe: {exc}"
            )
            summary = auth.get_student_analytics_summary(
                session['user_id'],
                pedido['id']
            )

    return render_template(
        'resultados.html',
        usuario=_usuario_sessao(),
        summary=summary,
        pedidos=pedidos,
        pedido=pedido,
        relatorios=relatorios,
        relatorios_erro=relatorios_erro
    )


@app.route(
    '/resultados/pedido/<int:order_id>/imagem/<image_name>'
)
def relatorio_pedido_imagem(order_id, image_name):
    """Imagem de relatório protegida por validação de propriedade."""
    pedido = _pedido_do_professor(order_id)

    if not pedido:
        abort(403)

    path = relatorio_pedido.get_report_image_path(order_id, image_name)

    if not path:
        try:
            resultado = relatorio_pedido.generate_order_reports(order_id)
        except Exception:
            abort(404)

        path = resultado.get('images', {}).get(image_name)

    if not path or not os.path.isfile(path):
        abort(404)

    return send_file(path, mimetype='image/png')


def _parse_datetime_local(value):
    """Converte um valor de <input type="datetime-local"> em datetime."""
    value = (value or "").strip()

    if not value:
        return None

    for formato in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, formato)
        except ValueError:
            continue

    raise ValueError("Data e hora inválidas.")


@app.route('/pedidos/novo', methods=['GET', 'POST'])
def pedido_diagnostico():
    """Página do professor para criar um pedido de diagnóstico."""
    if 'user_id' not in session:
        flash(
            "Por favor, faça login para criar um pedido de diagnóstico.",
            "warning"
        )
        return redirect(url_for('login'))

    if session.get('user_perfil') != 'professor':
        flash("Acesso restrito aos professores.", "warning")
        return redirect(url_for('dashboard'))

    professor = auth.get_teacher_by_user_id(session['user_id'])

    if not professor:
        flash(
            "Perfil de professor não encontrado para este usuário.",
            "danger"
        )
        return redirect(url_for('dashboard'))

    escolas = auth.get_teacher_schools(professor['id'])

    dados = {
        'title': '',
        'description': '',
        'school_id': str(escolas[0]['id']) if escolas else '',
        'grade': '',
        'class': '',
        'opening_date': datetime.now().strftime("%Y-%m-%dT%H:%M"),
        'closing_date': ''
    }

    if request.method == 'POST':
        for campo in dados:
            dados[campo] = request.form.get(campo, '')

        try:
            try:
                school_id = int(request.form.get('school_id', '') or 0)
            except (TypeError, ValueError):
                school_id = 0

            if not school_id:
                raise ValueError("Selecione a escola do pedido.")

            opening_date = (
                _parse_datetime_local(request.form.get('opening_date'))
                or datetime.now()
            )
            closing_date = _parse_datetime_local(
                request.form.get('closing_date')
            )

            auth.create_diagnostic_request(
                teacher_user_id=session['user_id'],
                school_id=school_id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                grade=request.form.get('grade'),
                school_class=request.form.get('class'),
                opening_date=opening_date,
                closing_date=closing_date
            )

            if opening_date > datetime.now():
                flash(
                    "Pedido de diagnóstico criado com sucesso! "
                    "Ele será aberto automaticamente em "
                    f"{opening_date.strftime('%d/%m/%Y às %H:%M')}.",
                    "success"
                )
            else:
                flash(
                    "Pedido de diagnóstico criado com sucesso e já está aberto! "
                    "Os estudantes da turma podem respondê-lo.",
                    "success"
                )
            return redirect(url_for('pedido_diagnostico'))

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Não foi possível criar o pedido: {e}", "danger")

    pedidos = auth.get_teacher_diagnostic_requests(professor['id'])

    # Turmas cadastradas por escola, usadas para sugerir série/turma no formulário.
    turmas_por_escola = {}

    for turma in auth.get_teacher_classes(professor['id']):
        turmas_por_escola.setdefault(
            str(turma['school_id']), []
        ).append({
            'grade': turma['grade'],
            'class': turma['class']
        })

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    return render_template(
        'pedido_diagnostico.html',
        usuario=usuario,
        professor=professor,
        escolas=escolas,
        pedidos=pedidos,
        dados=dados,
        turmas_por_escola=turmas_por_escola
    )


@app.route('/pedidos/<int:order_id>/status', methods=['POST'])
def alterar_status_pedido(order_id):
    """Encerra ou reabre um pedido de diagnóstico do próprio professor."""
    if 'user_id' not in session:
        flash(
            "Por favor, faça login para alterar o pedido.",
            "warning"
        )
        return redirect(url_for('login'))

    if session.get('user_perfil') != 'professor':
        flash("Acesso restrito aos professores.", "warning")
        return redirect(url_for('dashboard'))

    acao = (request.form.get('acao') or '').strip().lower()
    novo_status = {
        'encerrar': 'encerrado',
        'reabrir': 'aberto'
    }.get(acao)

    if not novo_status:
        flash("Ação inválida para o pedido de diagnóstico.", "danger")
        return redirect(url_for('pedido_diagnostico'))

    try:
        auth.update_diagnostic_request_status(
            session['user_id'],
            order_id,
            novo_status
        )

        if novo_status == 'encerrado':
            flash(
                "Pedido encerrado. Os estudantes não podem mais "
                "enviar ou alterar respostas.",
                "success"
            )
        else:
            pedido_atualizado = auth.get_teacher_diagnostic_request(
                session['user_id'], order_id
            )

            if (
                pedido_atualizado
                and pedido_atualizado['status'] == 'aguardando'
            ):
                flash(
                    "Pedido reaberto. Ele será disponibilizado "
                    "automaticamente na data de abertura "
                    f"({pedido_atualizado['abertura']}).",
                    "success"
                )
            else:
                flash(
                    "Pedido reaberto. Os estudantes já podem responder "
                    "novamente.",
                    "success"
                )
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash(f"Não foi possível atualizar o pedido: {e}", "danger")

    return redirect(url_for('pedido_diagnostico'))


@app.route('/questionario', methods=['GET', 'POST'])
def questionario():
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar o questionário.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    aluno = auth.get_student_by_user_id(user_id)

    # Se a conta não for de aluno (ex: professor logado), impede o acesso
    if not aluno:
        flash("Você precisa estar conectado como estudante para responder ao questionário.", "info")
        return redirect(url_for('dashboard'))

    pedidos = auth.get_available_diagnostic_requests(aluno['id'])

    # ------------------------------------------------------------
    # POST: gravação das respostas
    # ------------------------------------------------------------
    if request.method == 'POST':
        try:
            order_id = int(request.form.get('order_id', 0))
        except (TypeError, ValueError):
            order_id = 0

        pedido_post = auth.get_available_diagnostic_request(aluno['id'], order_id)

        if not pedido_post:
            flash(
                "Este diagnóstico não está disponível para você. "
                "Ele pode ter sido encerrado ou pertencer a outra turma.",
                "danger"
            )
            return redirect(url_for('questionario'))

        try:
            auth.save_questionnaire_response(aluno['id'], order_id, request.form)
            flash(
                "Suas respostas foram salvas com sucesso! Muito obrigado pela participação.",
                "success"
            )
            return redirect(url_for('minhas_respostas'))
        except Exception as e:
            flash(f"Ocorreu um erro ao salvar o questionário: {str(e)}", "danger")
            return redirect(url_for('questionario', pedido_id=order_id))

    # ------------------------------------------------------------
    # GET: lista de diagnósticos ou formulário do pedido escolhido
    # ------------------------------------------------------------
    pedido = None
    resposta = None
    pedido_id = request.args.get('pedido_id', type=int)

    if pedido_id:
        pedido = auth.get_available_diagnostic_request(aluno['id'], pedido_id)

        if not pedido:
            flash(
                "O diagnóstico selecionado não está mais disponível.",
                "warning"
            )
            return redirect(url_for('questionario'))

    if pedido and pedido['respondido']:
        resposta = auth.get_student_answer_detail(aluno['id'], pedido['id'])

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
        pedidos=pedidos,
        pedido=pedido,
        resposta=resposta
    )


@app.route('/minhas-respostas')
def minhas_respostas():
    """Histórico das respostas enviadas pelo próprio estudante."""
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar suas respostas.", "warning")
        return redirect(url_for('login'))

    aluno = auth.get_student_by_user_id(session['user_id'])

    if not aluno:
        flash("Você precisa estar conectado como estudante para acessar suas respostas.", "info")
        return redirect(url_for('dashboard'))

    respostas = auth.get_student_answers(aluno['id'])

    # Pedidos que o aluno ainda pode atualizar (abertos e da turma atual)
    pedidos_abertos = {
        pedido['id']
        for pedido in auth.get_available_diagnostic_requests(aluno['id'])
    }

    usuario = {
        'id': session['user_id'],
        'nome': session['user_nome'],
        'email': session['user_email'],
        'papel': session['user_perfil'],
        'perfil': session['user_perfil']
    }

    return render_template(
        'minhas_respostas.html',
        usuario=usuario,
        aluno=aluno,
        respostas=respostas,
        pedidos_abertos=pedidos_abertos
    )


@app.route('/perfil/completar', methods=['GET', 'POST'])
def completar_perfil():
    """
    Página de atualização de perfil obrigatória após o Primeiro Acesso.
    O usuário define seu novo username, e-mail e senha permanente.
    """
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar esta página.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        novo_username = request.form.get('novo_username', '').strip()
        email         = request.form.get('email', '').strip()
        nova_senha    = request.form.get('nova_senha', '')
        confirma      = request.form.get('confirma_senha', '')

        # Validações básicas
        if not novo_username or not email or not nova_senha:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("completar_perfil.html",
                                   usuario={'id': user_id, 'nome': session.get('user_nome'),
                                            'email': session.get('user_email'),
                                            'perfil': session.get('user_perfil')})

        if len(nova_senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("completar_perfil.html",
                                   usuario={'id': user_id, 'nome': session.get('user_nome'),
                                            'email': session.get('user_email'),
                                            'perfil': session.get('user_perfil')})

        if nova_senha != confirma:
            flash("As senhas não coincidem.", "danger")
            return render_template("completar_perfil.html",
                                   usuario={'id': user_id, 'nome': session.get('user_nome'),
                                            'email': session.get('user_email'),
                                            'perfil': session.get('user_perfil')})

        sucesso, msg = auth.atualizar_perfil(user_id, novo_username, email, nova_senha)
        if sucesso:
            # Atualiza a session com os novos dados
            session['user_nome'] = novo_username
            session['user_email'] = email
            session.pop('needs_profile_update', None)
            flash(msg, "success")
            return redirect(url_for('dashboard'))
        else:
            flash(msg, "danger")

    usuario = {
        'id': user_id,
        'nome': session.get('user_nome'),
        'email': session.get('user_email'),
        'perfil': session.get('user_perfil')
    }
    return render_template("completar_perfil.html", usuario=usuario)


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    start_server()



#Ferramenta de acesso do banco de dados

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