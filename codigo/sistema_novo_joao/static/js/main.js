/**
 * Plataforma Educacional de Metodologias Eficazes
 * Funções de máscara, validação, interatividade e filtros da interface
 */

document.addEventListener('DOMContentLoaded', () => {
    initCpfMask();
    initRoleSelector();
    initPasswordValidation();
    initPasswordToggle();
    initAutoDismissAlerts();
    initQuestionarioWorkHours();
    initResultadosFiltros();
    initDashboardAdminFiltros();
    initDbTerminal();
});

/**
 * 1. Máscara dinâmica para o campo CPF: 000.000.000-00
 */
function initCpfMask() {
    const cpfInputs = document.querySelectorAll('.cpf-mask, #cpf');
    cpfInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);

            if (value.length > 9) {
                value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
            } else if (value.length > 6) {
                value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
            } else if (value.length > 3) {
                value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
            }

            e.target.value = value;
        });
    });
}

/**
 * 2. Seletor visual de perfil (Admin, Professor, Estudante)
 */
function initRoleSelector() {
    const roleOptions = document.querySelectorAll('.role-option');
    const hiddenSelect = document.getElementById('perfil-select');

    if (!roleOptions.length || !hiddenSelect) return;

    roleOptions.forEach(option => {
        option.addEventListener('click', () => {
            roleOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            const selectedRole = option.getAttribute('data-role');
            if (selectedRole && hiddenSelect) {
                hiddenSelect.value = selectedRole;
            }
        });
    });
}

/**
 * 3. Validação de confirmação de senha
 */
function initPasswordValidation() {
    const senha = document.getElementById('senha');
    const confirma = document.getElementById('confirma_senha');
    const feedback = document.getElementById('senha-match-feedback');

    if (!senha || !confirma || !feedback) return;

    const checkMatch = () => {
        if (!confirma.value) {
            feedback.textContent = '';
            feedback.className = 'form-text mb-3';
            return;
        }

        if (senha.value === confirma.value) {
            feedback.textContent = '✓ As senhas conferem perfeitamente.';
            feedback.className = 'form-text text-success mb-3';
        } else {
            feedback.textContent = '✗ As senhas informadas não coincidem.';
            feedback.className = 'form-text text-danger mb-3';
        }
    };

    senha.addEventListener('input', checkMatch);
    confirma.addEventListener('input', checkMatch);
}

/**
 * 4. Alternador de visibilidade de senha (Olhinho)
 */
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            const icon = btn.querySelector('i');

            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    if (icon) {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                } else {
                    targetInput.type = 'password';
                    if (icon) {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                }
            }
        });
    });
}

/**
 * 5. Fechamento automático de alertas flash após 5 segundos
 */
function initAutoDismissAlerts() {
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {
                alert.style.display = 'none';
            }
        });
    }, 5000);
}

/**
 * 6. Questionário: Exibição condicional de horas de trabalho
 */
function initQuestionarioWorkHours() {
    const radioSim = document.getElementById('trab_sim');
    const radioNao = document.getElementById('trab_nao');
    const divWorkHours = document.getElementById('div_work_hours');

    if (!divWorkHours) return;

    const updateVisibility = () => {
        if (radioSim && radioSim.checked) {
            divWorkHours.style.display = 'block';
        } else {
            divWorkHours.style.display = 'none';
        }
    };

    if (radioSim) radioSim.addEventListener('change', updateVisibility);
    if (radioNao) radioNao.addEventListener('change', updateVisibility);
    updateVisibility();
}

// Suporte para chamadas diretas no onclick inline do questionário
window.toggleWorkHours = function(isWorking) {
    const div = document.getElementById('div_work_hours');
    if (div) {
        div.style.display = isWorking ? 'block' : 'none';
    }
};

/**
 * 7. Tela de Resultados: Filtros de busca por nome, turma e perfil pedagógico
 */
function initResultadosFiltros() {
    const inputNome = document.getElementById('filtro-nome');
    const selectTurma = document.getElementById('filtro-turma');
    const selectPerfil = document.getElementById('filtro-perfil');
    const btnLimpar = document.getElementById('btn-limpar-filtros');
    const linhas = document.querySelectorAll('.linha-estudante');
    const semResultados = document.getElementById('sem-resultados');
    const countBadge = document.getElementById('count-badge');

    if (!linhas.length || !inputNome) return;

    const totalEstudantes = linhas.length;

    function normalizar(texto) {
        return texto.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    }

    function filtrar() {
        const termoNome = normalizar(inputNome.value);
        const termoTurma = normalizar(selectTurma ? selectTurma.value : '');
        const termoPerfil = normalizar(selectPerfil ? selectPerfil.value : '');

        let visiveis = 0;

        linhas.forEach(linha => {
            const nome = normalizar(linha.getAttribute('data-nome') || '');
            const turma = normalizar(linha.getAttribute('data-turma') || '');
            const perfil = normalizar(linha.getAttribute('data-perfil') || '');

            const matchNome = !termoNome || nome.includes(termoNome);
            const matchTurma = !termoTurma || turma.includes(termoTurma);
            const matchPerfil = !termoPerfil || perfil.includes(termoPerfil);

            if (matchNome && matchTurma && matchPerfil) {
                linha.style.display = '';
                visiveis++;
            } else {
                linha.style.display = 'none';
            }
        });

        if (semResultados) semResultados.style.display = visiveis === 0 ? '' : 'none';
        if (countBadge) countBadge.textContent = `Mostrando ${visiveis} de ${totalEstudantes} alunos`;
    }

    inputNome.addEventListener('input', filtrar);
    if (selectTurma) selectTurma.addEventListener('change', filtrar);
    if (selectPerfil) selectPerfil.addEventListener('change', filtrar);

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            inputNome.value = '';
            if (selectTurma) selectTurma.value = '';
            if (selectPerfil) selectPerfil.value = '';
            filtrar();
        });
    }
}

/**
 * 8. Dashboard Admin: Filtragem da tabela de usuários
 */
function initDashboardAdminFiltros() {
    const inputBusca = document.getElementById('filtro-admin-busca');
    const selectPerfil = document.getElementById('filtro-admin-perfil');
    const btnLimpar = document.getElementById('btn-admin-limpar');
    const linhas = document.querySelectorAll('.linha-admin-user');
    const semUsuarios = document.getElementById('sem-usuarios-admin');
    const countBadge = document.getElementById('admin-user-count');

    if (!linhas.length || !inputBusca) return;

    const totalUsuarios = linhas.length;

    function normalizar(texto) {
        return texto.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    }

    function filtrarUsuarios() {
        const termoBusca = normalizar(inputBusca.value);
        const perfilSelecionado = normalizar(selectPerfil ? selectPerfil.value : '');

        let visiveis = 0;

        linhas.forEach(linha => {
            const nome = normalizar(linha.getAttribute('data-nome') || '');
            const email = normalizar(linha.getAttribute('data-email') || '');
            const perfil = normalizar(linha.getAttribute('data-perfil') || '');

            const matchBusca = !termoBusca || nome.includes(termoBusca) || email.includes(termoBusca);
            const matchPerfil = !perfilSelecionado || perfil === perfilSelecionado;

            if (matchBusca && matchPerfil) {
                linha.style.display = '';
                visiveis++;
            } else {
                linha.style.display = 'none';
            }
        });

        if (semUsuarios) semUsuarios.style.display = visiveis === 0 ? '' : 'none';
        if (countBadge) countBadge.textContent = `Mostrando ${visiveis} de ${totalUsuarios} cadastrados`;
    }

    inputBusca.addEventListener('input', filtrarUsuarios);
    if (selectPerfil) selectPerfil.addEventListener('change', filtrarUsuarios);

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            inputBusca.value = '';
            if (selectPerfil) selectPerfil.value = '';
            filtrarUsuarios();
        });
    }
}

/**
 * 9. Terminal DB (/db): Execução assíncrona de comandos SQL
 */
function initDbTerminal() {
    const terminal = document.getElementById("terminal");
    const command = document.getElementById("command");

    if (!terminal || !command) return;

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag));
    }

    command.addEventListener("keydown", async function(event) {
        if (event.key !== "Enter") return;
        event.preventDefault();

        const text = command.value;
        if (!text.trim()) return;

        terminal.innerHTML += `<span class="input">db&gt; ${escapeHTML(text)}</span>\n`;
        command.value = "";

        try {
            const response = await fetch("/db/execute", {
                method: "POST",
                headers: { "Content-Type": "text/plain" },
                body: text
            });

            const result = await response.text();
            terminal.innerHTML += escapeHTML(result) + "\n";
        } catch (error) {
            terminal.innerHTML += `<span class="error">${escapeHTML(error.toString())}</span>\n`;
        }

        terminal.scrollTop = terminal.scrollHeight;
    });
}
