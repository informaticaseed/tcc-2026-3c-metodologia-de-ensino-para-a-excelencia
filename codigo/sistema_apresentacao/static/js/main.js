/**
 * Plataforma Educacional de Metodologias Eficazes
 * Funções de máscara, validação e interatividade da interface
 */

document.addEventListener('DOMContentLoaded', () => {
    initCpfMask();
    initRoleSelector();
    initPasswordValidation();
    initPasswordToggle();
    initAutoDismissAlerts();
});

/**
 * Máscara dinâmica para o campo CPF: 000.000.000-00
 */
function initCpfMask() {
    const cpfInputs = document.querySelectorAll('.cpf-mask');
    cpfInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, ''); // Apenas números
            if (value.length > 11) {
                value = value.slice(0, 11);
            }

            // Aplica a máscara progressivamente
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
 * Seletor visual de perfil (Admin, Professor, Estudante)
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
            hiddenSelect.value = selectedRole;
        });
    });

    // Sincroniza estado inicial se já houver valor selecionado
    if (hiddenSelect.value) {
        const currentActive = document.querySelector(`.role-option[data-role="${hiddenSelect.value}"]`);
        if (currentActive) {
            roleOptions.forEach(opt => opt.classList.remove('active'));
            currentActive.classList.add('active');
        }
    }
}

/**
 * Validação de correspondência de senha em tempo real
 */
function initPasswordValidation() {
    const senhaInput = document.getElementById('senha');
    const confirmaInput = document.getElementById('confirma_senha');
    const feedbackMsg = document.getElementById('senha-match-feedback');

    if (!senhaInput || !confirmaInput || !feedbackMsg) return;

    function checkPasswords() {
        if (!confirmaInput.value) {
            feedbackMsg.textContent = '';
            feedbackMsg.className = 'form-text';
            return;
        }

        if (senhaInput.value === confirmaInput.value) {
            feedbackMsg.textContent = '✓ As senhas conferem.';
            feedbackMsg.className = 'form-text text-success fw-semibold';
        } else {
            feedbackMsg.textContent = '✗ As senhas não conferem.';
            feedbackMsg.className = 'form-text text-danger fw-semibold';
        }
    }

    senhaInput.addEventListener('input', checkPasswords);
    confirmaInput.addEventListener('input', checkPasswords);
}

/**
 * Alternar visibilidade de senha (mostrar / ocultar)
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
 * Fechamento automático de alertas flash após 5 segundos
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

