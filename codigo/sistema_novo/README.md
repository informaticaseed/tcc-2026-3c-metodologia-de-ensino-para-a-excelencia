# Plataforma Educacional de Metodologias Eficazes de Ensino-Aprendizagem

Sistema web desenvolvido com **Python (Flask)**, **HTML5 / Bootstrap 5**, **PostgreSQL** e **Data Analytics / Machine Learning** (PCA e K-Means) para diagnóstico estudantil multidimensional, cadastro, autenticação e acompanhamento de turmas e perfis em uma plataforma educacional com foco em metodologias ativas.

---

## 🚀 Arquitetura e Funcionalidades

1. **Perfis de Usuário**:
   - 🛡️ **Administrador**: Visão geral de métricas, gestão de todos os usuários registrados no banco de dados e acesso aos resultados analíticos consolidados.
   - 👨‍🏫 **Professor**: Painel pedagógico, acompanhamento de diagnósticos e turmas.
   - 🎓 **Estudante**: Questionário diagnóstico multidimensional, trilhas de aprendizagem e desafios.

2. **Banco de Dados Relacional (PostgreSQL)**:
   - Esquema dedicado: `sc_student_diagnosis`.
   - Tabelas estruturadas:
     - `users`, `teachers`, `student`
     - `diagnostic_requests`, `diagnosis_answer`
     - Dimensões do Diagnóstico: `socioeconomic_data`, `cultural_context`, `political_dimension`, `school_experiences`, `expectations_dreams`
     - Data Mart Analítico: `student_analytics` (indicadores de 0 a 10, agrupamento K-Means e coordenadas PCA).

---

## 📦 Guia para Desenvolvedores (Como Rodar o Projeto)

### 1. Clonar e Instalar as Dependências
Abra o terminal na pasta `sistema_apresentacao` e instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### 2. Configurar o Ambiente (.env)
O projeto já conta com o arquivo `.env.example`. Crie ou edite o seu `.env` com a sua senha do PostgreSQL local caso seja diferente:
```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=sistema
DB_USER=postgres
DB_PASSWORD=1234
DB_SCHEMA=sc_student_diagnosis
SECRET_KEY=tcc-metodologia-ensino-excelencia-secret-key-2026
```

### 3. Inicializar o Banco de Dados Automaticamente
Execute o script de inicialização:
```bash
python database/init_db.py
```
> **Nota para o desenvolvedor:** Este comando cria automaticamente o banco de dados `sistema` (caso ele não exista no seu PostgreSQL), executa o DDL de tabelas, insere as 15 contas de alunos sintéticos e gera as credenciais de teste.

### 4. Iniciar a Aplicação Web
Você pode iniciar a aplicação executando diretamente da raiz:
```bash
python app.py
```
*(ou se preferir: `python backend/main.py`)*

### 5. Acessar no Navegador
Abra: **[http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)**

---

## 🔑 Contas Pré-cadastradas para Testes

| Perfil | Nome | E-mail | Senha |
| :--- | :--- | :--- | :--- |
| **Administrador Geral** | Administrador Geral | `admin@escola.com` | `admin123` |
| **Professora** | Maria da Silva Santos | `maria.prof@escola.com` | `hash_prof` |
| **Estudante** | Henry Gabriel Alves Sousa | `henrygabriel.sousa@escola.com` | `hash_aluno` |
| **Estudante** | Yan da Cruz Câmara | `yan.camara@escola.com` | `hash_aluno` |
| **Estudante** | Lavínia Andrade Alves | `lavinia.alves@escola.com` | `hash_aluno` |
