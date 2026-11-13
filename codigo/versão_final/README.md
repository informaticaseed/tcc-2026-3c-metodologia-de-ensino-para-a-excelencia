# Plataforma Educacional de Metodologias Eficazes de Ensino-Aprendizagem (TCC 2026)

Sistema web desenvolvido com **Python (Flask)**, **PostgreSQL**, **HTML5 / Bootstrap 5** e pipeline de **Data Analytics / Machine Learning** (K-Means e PCA) para diagnóstico estudantil multidimensional, cadastro institucional, autenticação e acompanhamento de turmas e perfis orientados a metodologias ativas.

---

## 🚀 Arquitetura e Modelagem de Dados

### 1. Perfis de Acesso e Entidades:
- 🏫 **Instituições de Ensino (`schools`)**: Registro de escolas/unidades com código INEP.
- 🛡️ **Superadmin**: maior nível de acesso. **Não possui instituição vinculada** (`school_id = NULL`). Responsável por cadastrar as **instituições de ensino** e os **administradores** (um admin por instituição).
- 🛡️ **Admin (Gestor Escolar)**: **sempre vinculado a uma instituição** (`school_id` obrigatório). Responsável por cadastrar **professores e estudantes apenas da própria escola**.
- 👨‍🏫 **Professor (`teachers` & `teacher_schools`)**: Modelo relacional N:N permitindo que um professor lecione em múltiplas instituições de ensino, abra pedidos de diagnóstico e acompanhe o perfil de suas turmas.
- 🎓 **Estudante (`student`)**: Aluno vinculado à sua instituição, série e turma. O sistema atende exclusivamente ao **Ensino Médio** (1º, 2º e 3º ano). Conta com fluxo de **Primeiro Acesso / Ativação de Conta**.

### 2. Banco de Dados Relacional (PostgreSQL):
- **Schema:** `sc_student_diagnosis`
- **Estrutura de Tabelas:**
  - `schools`: Instituições de ensino registradas.
  - `users`: Contas de autenticação (UUID, username, e-mail, senha, status de ativação `is_active` e vínculo institucional).
  - `teachers` & `teacher_schools`: Cadastro docente e vínculos com múltiplas escolas.
  - `student`: Alunos vinculados a escolas.
  - `diagnostic_requests` & `diagnosis_answer`: Pedidos de diagnóstico abertos por professores e cabeçalhos de resposta dos estudantes.
  - **Dimensões do Diagnóstico:** `socioeconomic_data`, `cultural_context`, `school_experiences`, `expectations_dreams`.
  - **Data Mart Analítico (`student_analytics`):** Indicadores normalizados de 0 a 10, agrupamento K-Means (clusters pedagógicos) e projeção vetorial PCA 2D.

### 3. Estrutura Frontend & Separação de Responsabilidades:
- **Padrão SoC (*Separation of Concerns*):** Todos os scripts JavaScript foram desacoplados dos arquivos HTML e organizados em módulos externos em `static/js/`:
  - `static/js/main.js`: Visibilidade de senhas, exibição condicional do questionário e filtragem em tempo real nos dashboards de resultados e administração.
  - `static/js/terminal.js`: Comunicação assíncrona com o terminal de consultas SQL do PostgreSQL.

### 4. Configuração Acadêmica Centralizada:
- As séries e turmas atendidas pelo sistema ficam em **`backend/academico.py`**.
- Alterar esse arquivo atualiza automaticamente os formulários e as validações do backend, evitando listas duplicadas pelo projeto.
- O backend valida tanto a série (`serie_valida`) quanto a turma (`turma_valida`) antes de gravar estudantes e pedidos de diagnóstico.
- Depois de mudar as séries, execute `python database/verificar_academico.py` para listar registros antigos do banco que ainda usam séries ou turmas fora da configuração atual. O script apenas diagnostica; a correção dos dados deve ser feita manualmente (ou recriando a base de demonstração).

---

## 🔐 LGPD, Termos de Uso e Política de Privacidade

A plataforma disponibiliza dois documentos acessíveis pelo rodapé de todas as
páginas e pelo formulário de primeiro acesso:

- **Termos de Uso:** [/termos-de-uso](http://127.0.0.1:5000/termos-de-uso)
- **Política de Privacidade:** [/politica-de-privacidade](http://127.0.0.1:5000/politica-de-privacidade)

No primeiro acesso, o usuário precisa aceitar os Termos de Uso e declarar que
leu e compreendeu a Política de Privacidade. Os documentos contêm seções
específicas sobre crianças e adolescentes (LGPD, Art. 14).

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
> 3. Popula a base com a escola padrão, turmas e alunos de demonstração (`database/dados_revisada.sql`).
> 4. Configura a conta do Superadmin (sem instituição vinculada).
> 5. Executa a pipeline de análise de dados (K-Means/PCA) e persiste os indicadores em `student_analytics`.
> 6. Gera os gráficos em diretório protegido (`backend/relatorios_globais/`), fora de `static/`.

> **Seed idempotente:** `database/dados_revisada.sql` usa `INSERT ... SELECT ... WHERE NOT EXISTS` nas tabelas com `GENERATED ALWAYS AS IDENTITY`, de modo que executar o script várias vezes não consome IDs das sequences. O pipeline de análise aplica a mesma ideia em `student_analytics`: primeiro `UPDATE` e, só quando a resposta ainda não possui analytics, um `INSERT`. Assim, reexecutar `init_db.py` não abre buracos nos contadores.

### 5. Iniciar o Servidor Web Flask
Execute na raiz do projeto:
```bash
python app.py
```
O servidor estará disponível em: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Credenciais Pré-configuradas para Testes

| Perfil | Nome | E-mail | Senha / Status |
| :--- | :--- | :--- | :--- |
| **Superadmin** | Administrador Geral | `admin@escola.com` | `admin123` |
| **Admin (Escola 1)** | José Administrador | `jose.admin@escola.com` | `Teste@2026` |
| **Professora** | Maria da Silva Santos | `maria.prof@escola.com` | `Teste@2026` |
| **Estudante (Ativo)** | Lorenzo Nogueira Vasconcelos | `lorenzo.vasconcelos@escola.com` | `Teste@2026` |
| **Estudante (Ativo)** | Pietra Machado Campos | `pietra.campos@escola.com` | `Teste@2026` |
| **Estudante (Ativo)** | Henry Gabriel Alves Sousa | Código: `Henry Gabriel` | `123456` |
| **Estudante (Primeiro Acesso)** | Yan da Cruz Câmara | Código: `yan_camara` | `PrimeiroAcesso@2026` |

### Níveis de acesso administrativos

| Ação | Superadmin | Admin (Gestor Escolar) |
| :--- | :---: | :---: |
| Cadastrar instituições de ensino | ✅ | ❌ |
| Cadastrar administradores | ✅ | ❌ |
| Cadastrar professores | ❌ | ✅ (somente na própria escola) |
| Cadastrar estudantes | ❌ | ✅ (somente na própria escola) |
| Ver todos os usuários do sistema | ✅ | ❌ (apenas a própria escola) |
| Acessar resultados de diagnóstico | ❌ | ❌ |

As telas de gestão ficam em:

- **[http://127.0.0.1:5000/admin/escolas](http://127.0.0.1:5000/admin/escolas)** — exclusiva do superadmin: cadastro e listagem das instituições (nome e código INEP obrigatório).
- **[http://127.0.0.1:5000/admin/usuarios](http://127.0.0.1:5000/admin/usuarios)** — superadmin cadastra administradores; admin cadastra professores e estudantes da própria escola.

Regras aplicadas no backend (não apenas na interface):

- O superadmin não tem `school_id` e só pode criar contas com perfil `admin`, sempre vinculadas a uma instituição existente.
- O admin tem `school_id` obrigatório e só pode criar `professor` ou `aluno`; qualquer `school_id` enviado pelo formulário é ignorado e substituído pela escola do admin.
- Contas criadas pelo admin nascem inativas, com senha temporária, e passam pelo **Primeiro Acesso**. Administradores criados pelo superadmin já nascem ativos, com senha em bcrypt.

### Fluxo de acesso

> A tabela acima representa o estado de uma base recém-inicializada. Se uma conta de primeiro acesso já tiver sido ativada, ela passa a usar a página de login normalmente.

- **Conta já ativada** (`is_active = TRUE`): use **[http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)** com usuário/e-mail e senha.
- **Conta pendente de primeiro acesso** (`is_active = FALSE`): use **[http://127.0.0.1:5000/cadastro](http://127.0.0.1:5000/cadastro)** com o código de acesso e a senha temporária.
- O primeiro acesso **ativa** a conta, autentica o usuário e direciona imediatamente para `/perfil/completar`, onde ele define usuário, e-mail e senha definitivos.
- Enquanto o perfil não for concluído, o acesso às demais páginas da plataforma fica bloqueado.
- Se a página de primeiro acesso informar que a conta **já foi ativada**, use a página de login.
- Se o login informar que a conta **ainda não foi ativada**, use a página de primeiro acesso.

---

## 📝 Pedidos de Diagnóstico (Professor)

Professores autenticados podem criar pedidos de diagnóstico em uma página dedicada:

**[http://127.0.0.1:5000/pedidos/novo](http://127.0.0.1:5000/pedidos/novo)**

O formulário grava diretamente na tabela `diagnostic_requests` e contempla:

- **Título** (`title`) e **descrição** (`description`);
- **Escola** (`school_id`), limitada às escolas vinculadas ao professor em `teacher_schools`;
- **Série** (`grade`) e **turma** (`class`);
- **Data de abertura** (`opening_date`) e **data de encerramento** (`closing_date`, opcional).

O `teacher_id` é obtido automaticamente a partir do professor logado — não é possível indicar outro professor como responsável. Todo pedido é criado com `status = 'aberto'` e não existe campo manual de situação: o estado é determinado pelas datas.

- Se a **data de abertura** estiver no futuro, o pedido permanece fechado (não aparece para os alunos) e abre automaticamente quando a data for atingida.
- Se a **data de abertura** já tiver passado, o pedido fica disponível imediatamente.

Na seção **Meus pedidos de diagnóstico**, o professor pode:

- consultar os resultados de qualquer pedido seu, aberto ou encerrado;
- **encerrar** um pedido antes do prazo, interrompendo novas respostas;
- **cancelar a abertura** de um pedido que ainda não começou;
- **reabrir** um pedido encerrado manualmente, desde que a data de encerramento ainda não tenha sido atingida.

Quando a **data de encerramento** é atingida, o pedido é fechado automaticamente pelo sistema. A partir daí:

- o aluno não vê mais o pedido na lista de questionários e não pode enviar ou alterar respostas;
- o aluno continua acessando o que já respondeu em **Minhas Respostas**;
- o professor continua acessando normalmente os resultados e relatórios do pedido.

A página também lista os pedidos já criados pelo professor e indica as turmas cadastradas em `teacher_classes` para cada escola.

---

## 🎓 Diagnósticos e Respostas (Estudante)

O estudante autenticado acessa:

- **[http://127.0.0.1:5000/questionario](http://127.0.0.1:5000/questionario)** — lista **todos** os pedidos de diagnóstico abertos para a sua escola, série e turma;
- **[http://127.0.0.1:5000/minhas-respostas](http://127.0.0.1:5000/minhas-respostas)** — histórico das respostas já enviadas.

Comportamento da lista de diagnósticos:

- cada pedido aberto e compatível com a turma aparece como uma opção;
- o estudante pode responder a quantos diagnósticos existirem para a sua turma;
- pedidos já respondidos continuam visíveis e podem ser atualizados enquanto estiverem abertos;
- o formulário é pré-preenchido com as respostas anteriores;
- pedidos de outras escolas, séries ou turmas não aparecem e não podem ser respondidos pela URL;
- o histórico exibe apenas as respostas do próprio estudante, agrupadas por pedido, com data de envio e todos os campos respondidos.

> A base de demonstração possui inicialmente **um pedido por turma**. Para visualizar múltiplas opções, crie novos pedidos para a mesma série/turma em `/pedidos/novo`. Todos passarão a aparecer automaticamente para os estudantes daquela turma.

---

## 💻 Terminal Interativo do Banco de Dados (`/db`)

O sistema disponibiliza um terminal SQL web acessível em: **[http://127.0.0.1:5000/db](http://127.0.0.1:5000/db)**

Comandos úteis para demonstração e inspeção do banco:
- `\dt` : Lista todas as tabelas do esquema `sc_student_diagnosis`.
- `\d student` : Exibe as colunas e tipos da tabela de alunos.
- `SELECT COUNT(*) FROM student;` : Conta o total de estudantes cadastrados.
- `SELECT * FROM student_analytics LIMIT 5;` : Consulta os resultados gerados pelo K-Means/PCA.

---

## 📊 Visualização dos Resultados Analíticos

A página **[http://127.0.0.1:5000/resultados](http://127.0.0.1:5000/resultados)** é exclusiva de professores e apresenta os resultados **separados por pedido de diagnóstico**:

- um seletor permite alternar entre os pedidos criados pelo próprio professor;
- os cards de médias e a tabela de estudantes consideram somente as respostas do pedido selecionado;
- PCA, K-Means e gráficos são recalculados e gerados por pedido, sob demanda, com cache em JSON invalidado automaticamente quando novas respostas chegam;
- o professor só acessa pedidos vinculados ao seu usuário (validado no servidor em todas as rotas).

Os arquivos analíticos ficam fora de `static/`, em diretórios protegidos:

- `backend/relatorios_globais/` — visão global gerada pelo pipeline;
- `backend/relatorios_pedidos/pedido_<id>/` — relatórios de cada pedido.

As imagens são servidas apenas pela rota autenticada `/resultados/pedido/<id>/imagem/<nome>`, que verifica a propriedade do pedido antes de entregar o arquivo.

Relatórios gerados por pedido:
1. **PCA 2D:** Mapeamento de dispersão dos perfis estudantis (`grafico_clusters_pca.png`).
2. **Dimensões por Cluster:** Comparativo das 4 dimensões pedagógicas de 0 a 10 (`grafico_dimensoes_clusters.png`).
3. **Análise por Turma:** Médias comparativas da turma do pedido (`analise_por_turma.png`).
4. **Nuvens de Palavras:** Eixos qualitativos de dificuldades, sonhos e apoio da escola (`nuvens_palavras_segmentadas.png`).
