# Plataforma Educacional de Metodologias Eficazes de Ensino-Aprendizagem (TCC 2026)

Sistema web desenvolvido com **Python (Flask)**, **PostgreSQL**, **HTML5 / Bootstrap 5** e pipeline de **Data Analytics / Machine Learning** (K-Means e PCA) para diagnóstico estudantil multidimensional, cadastro institucional, autenticação e acompanhamento de turmas e perfis orientados a metodologias ativas.

---

## 🚀 Arquitetura e Modelagem de Dados

### 1. Perfis de Acesso e Entidades:
- 🏫 **Instituições de Ensino (`schools`)**: Registro de escolas/unidades com código INEP, cidade e estado.
- 🛡️ **Administrador**: Gestão do sistema, visão geral de métricas, gestão de usuários e acesso aos resultados analíticos consolidados. Pode ser Superadmin ou Gestor vinculado a uma escola.
- 👨‍🏫 **Professor (`teachers` & `teacher_schools`)**: Modelo relacional N:N permitindo que um professor lecione em múltiplas instituições de ensino, abra pedidos de diagnóstico e acompanhe o perfil de suas turmas.
- 🎓 **Estudante (`student`)**: Aluno vinculado à sua instituição, série e turma. Conta com suporte a identificação por CPF, data de nascimento e fluxo de **Primeiro Acesso / Ativação de Conta**.

### 2. Banco de Dados Relacional (PostgreSQL):
- **Schema:** `sc_student_diagnosis`
- **Estrutura de Tabelas:**
  - `schools`: Instituições de ensino registradas.
  - `users`: Contas de autenticação (UUID, username, CPF, e-mail, senha, status de ativação `is_active` e vínculo institucional).
  - `teachers` & `teacher_schools`: Cadastro docente e vínculos com múltiplas escolas.
  - `student`: Alunos vinculados a escolas, com CPF e data de nascimento.
  - `diagnostic_requests` & `diagnosis_answer`: Pedidos de diagnóstico abertos por professores e cabeçalhos de resposta dos estudantes.
  - **Dimensões do Diagnóstico:** `socioeconomic_data`, `cultural_context`, `political_dimension`, `school_experiences`, `expectations_dreams`.
  - **Data Mart Analítico (`student_analytics`):** Indicadores normalizados de 0 a 10, agrupamento K-Means (clusters pedagógicos) e projeção vetorial PCA 2D.

---

## 📦 Guia Rápido de Instalação e Execução

### 1. Pré-requisitos
- **Python 3.10+** instalado.
- **PostgreSQL 14+** em execução no computador (porta padrão: `5432`).

### 2. Instalação das Dependências
Na raiz do projeto (`sistema_novo`), instale as bibliotecas Python:
```bash
pip install -r requirements.txt
```

### 3. Configuração do Ambiente (`.env`)
Copie o arquivo de exemplo ou crie o `.env` na raiz do projeto com as credenciais do seu banco de dados PostgreSQL local:
```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=sistema
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_SCHEMA=sc_student_diagnosis
SECRET_KEY=tcc-metodologia-ensino-excelencia-secret-key-2026
```

### 4. Inicialização Automatizada do Banco de Dados
Execute o script único de inicialização:
```bash
python database/init_db.py
```
> **O que este script faz:**
> 1. Cria o banco de dados `sistema` no PostgreSQL caso ainda não exista.
> 2. Executa a estrutura DDL completa (`database/estrutura_revisada.sql`).
> 3. Popula a base com a escola padrão, turmas e alunos sintéticos (`database/dados_revisada.sql`).
> 4. Configura a conta do Administrador Geral.
> 5. Executa a pipeline de análise de dados (K-Means/PCA) e persiste os indicadores em `student_analytics`.
> 6. Sincroniza os gráficos gerados na pasta `static/relatorios/`.

*(Opcional: Para gerar novos dados sintéticos aleatórios com Faker, execute `python database/gerar_dados_sinteticos.py`).*

### 5. Iniciar o Servidor Web Flask
Execute na raiz do projeto:
```bash
python app.py
```
O servidor estará disponível em: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Credenciais Pré-configuradas para Testes

| Perfil | Nome | CPF | E-mail | Senha / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Administrador Geral** | Administrador | `000.000.000-00` | `admin@escola.com` | `admin123` |
| **Professora** | Maria da Silva Santos | `111.222.333-44` | `maria.prof@escola.com` | `hash_prof` |
| **Estudante (Ativo)** | Agatha Abreu Teixeira | `265.917.803-86` | `agatha.teixeira@escola.com` | `hash_aluno` |
| **Estudante (Ativo)** | Samuel Castro Martins | `643.520.187-08` | `samuel.martins@escola.com` | `hash_aluno` |
| **Estudante (Primeiro Acesso)** | Henry Gabriel Alves Sousa | `438.150.926-98` | `henrygabriel.sousa@escola.com` | *Aguardando Ativação (`is_active=False`)* |
| **Estudante (Primeiro Acesso)** | Bento Borges Cunha | `380.416.975-93` | `bento.cunha@escola.com` | *Aguardando Ativação (`is_active=False`)* |

---

## 📊 Visualização dos Resultados Analíticos
Os gráficos comparativos gerados pelo pipeline de Machine Learning são armazenados em `static/relatorios/` e integrados diretamente no painel web (`/resultados`):
1. **PCA 2D:** Mapeamento de dispersão dos perfis estudantis (`grafico_clusters_pca.png`).
2. **Dimensões por Cluster:** Comparativo das 5 dimensões pedagógicas de 0 a 10 (`grafico_dimensoes_clusters.png`).
3. **Análise por Turma:** Médias comparativas entre séries e turmas (`analise_por_turma.png`).
4. **Nuvens de Palavras:** Eixos qualitativos de dificuldades, sonhos e apoio da escola (`nuvens_palavras_segmentadas.png`).
