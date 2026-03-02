# PLATAFORMA DE REVISÃO INTELIGENTE POR MATÉRIAS

Sistema web voltado para organização inteligente de revisões acadêmicas, permitindo que estudantes registrem disciplinas, acompanhem tópicos estudados, realizem revisões com reflexão escrita e priorizem automaticamente o que deve ser estudado diariamente.

Além disso, a plataforma oferece uma visão pedagógica para professores, permitindo o acompanhamento do engajamento da turma e a identificação de dificuldades recorrentes.

---

## 🎯 Visão do Produto

A Plataforma de Revisão Inteligente por Matérias foi concebida para resolver um problema comum no contexto educacional: a dificuldade em manter revisões sistemáticas ao longo do semestre.

O sistema permite que:

- 📚 Alunos organizem disciplinas e tópicos estudados  
- ✅ Registrem revisões com reflexão em texto livre  
- 📅 Recebam uma lista priorizada “Estudar Hoje”  
- 📊 Acompanhem histórico de revisões  
- 👩‍🏫 Professores visualizem indicadores de engajamento e dificuldades  

A proposta une organização acadêmica com acompanhamento pedagógico estruturado.

---

## 🏗 Arquitetura do Sistema

A aplicação segue o modelo Cliente-Servidor, dividido em três camadas principais:

Usuário → Front-end (Angular) → API (FastAPI) → Banco de Dados (MySQL)

- O Front-end é responsável pela interface e interação com o usuário.
- A API centraliza regras de negócio, autenticação e persistência.
- O Banco de Dados armazena usuários, disciplinas, tópicos e registros de revisão.

A comunicação ocorre via API REST utilizando JSON.

---

## 🧱 Stack Tecnológica

### Back-end
- Python
- FastAPI
- SQLAlchemy (ORM)
- MySQL
- JWT (python-jose)
- bcrypt (passlib)
- SlowAPI (rate limiting)

### Integração
- Comunicação REST
- Autenticação Bearer Token
- CORS configurado para integração com o Front-end

---

## 🔐 Autenticação e Segurança

A autenticação é baseada em JWT (JSON Web Token) com as seguintes características:

- 🔑 Token assinado com SECRET_KEY
- ⏳ Expiração configurável
- 🛡 Controle de acesso por perfil (role: aluno/professor)
- 🚪 Logout com invalidação real via blacklist persistida no banco
- 🔒 Senhas armazenadas com hash seguro utilizando bcrypt
- 🚦 Rate limiting aplicado em endpoints sensíveis (/login e /register)

### Fluxo de Autenticação

1. Usuário realiza login.
2. API valida credenciais.
3. JWT é gerado contendo:
   - email (sub)
   - role
   - expiração
4. Front-end armazena token e o envia automaticamente nas próximas requisições.
5. Endpoints protegidos validam assinatura, expiração, blacklist e existência do usuário.

---

## 🚀 Principais Funcionalidades

### 👤 Gestão de Usuários
- Cadastro e autenticação com perfis distintos (Aluno / Professor)
- Controle de acesso baseado em papel

### 📚 Gestão de Disciplinas
- CRUD completo de disciplinas
- Organização personalizada por aluno

### 📝 Gestão de Tópicos
- Registro de tópicos estudados por disciplina
- Edição e exclusão de registros

### 🔁 Sistema de Revisão com Reflexão
- Marcação de tópico como revisado
- Registro de data e hora
- Campo de reflexão em texto livre

### 📅 Lista “Estudar Hoje”
- Priorização de tópicos:
  - Atrasados
  - Nunca revisados
  - Com base em revisões anteriores

### 📊 Histórico de Revisões
- Registro cronológico completo
- Visualização de progresso individual

### 👩‍🏫 Dashboard Pedagógico
- Indicadores de engajamento da turma
- Identificação de alunos com revisões atrasadas
- Visualização de tópicos com maior índice de dificuldade

---

## 📁 Estrutura do Projeto

app/  
├── core/  
├── database/  
├── models/  
├── schemas/  
├── services/  
├── routers/  
main.py  

- core/: configurações e segurança  
- database/: conexão com banco e base ORM  
- models/: entidades do sistema  
- schemas/: validação de dados  
- services/: regras de negócio  
- routers/: endpoints da API  

---

## ⚙️ Execução Local

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/cauagms/plataforma-revisao-back.git
cd plataforma-revisao-back
```

### 2️⃣ Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha

SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=http://localhost:4200
```

### 5️⃣ Executar a aplicação

```bash
uvicorn main:app --reload
```

API disponível em:  
http://localhost:8000  

Documentação automática (Swagger):  
http://localhost:8000/docs
