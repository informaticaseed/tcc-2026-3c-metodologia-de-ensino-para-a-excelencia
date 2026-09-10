# Plataforma Educacional de Metodologias Eficazes de Ensino-Aprendizagem

Sistema web desenvolvido com **Python (Flask)**, **HTML5**, **CSS3 (Bootstrap 5)**, **JavaScript** e **SQLite** para cadastro, autenticação e gerenciamento de perfis em uma plataforma educacional com foco em metodologias ativas.

---

## 🚀 Funcionalidades

1. **Perfis de Usuário**:
   - 🛡️ **Administrador**: Visão geral de métricas, gestão de todos os usuários registrados.
   - 👨‍🏫 **Professor**: Ferramentas didáticas, criação de planos de aula e acompanhamento de turmas.
   - 🎓 **Estudante**: Acesso a trilhas de aprendizagem, desafios gamificados e debates.

2. **Tela de Cadastro**:
   - Campos: **Nome Completo**, **E-mail**, **CPF** (com máscara automática `000.000.000-00` e validação), **Perfil de Acesso** e **Senha**.
   - Validações de e-mail e CPF duplicados no banco de dados.
   - Validação de senha em tempo real.

3. **Tela de Login**:
   - Acesso seguro por **E-mail** ou **CPF** + Senha criptografada (`generate_password_hash` / `werkzeug.security`).
   - Sessão segura (`Flask Session`) e proteção de rotas privadas.

4. **Painel / Dashboard**:
   - Conteúdo dinâmico de acordo com o perfil logado.
   - Catálogo de Metodologias Ativas (PBL, Sala de Aula Invertida, Gamificação, Peer Instruction, Design Thinking, Microlearning).

---

## 📦 Como Executar o Projeto

### 1. Instalar as dependências
Abra o terminal (PowerShell / Prompt de Comando) nesta pasta e execute:
```bash
pip install -r requirements.txt
```

### 2. Iniciar a aplicação Flask
Execute:
```bash
python app.py
```

### 3. Acessar no Navegador
Abra o seu navegador e acesse:
```
http://127.0.0.1:5000
```

---

## 🔑 Contas de Demonstração (Pré-cadastradas)

O sistema inicializa automaticamente contas de teste caso o banco esteja novo:

| Perfil | E-mail | Senha |
| :--- | :--- | :--- |
| **Administrador** | `admin@metodologias.com` | `admin123` |
| **Professor** | `carlos.professor@metodologias.com` | `prof123` |
| **Estudante** | `mariana.estudante@metodologias.com` | `aluno123` |

