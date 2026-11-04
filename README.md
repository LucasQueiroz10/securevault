# SecureVault

Cofre de senhas full stack (desktop + API), desenvolvido como projeto de aprendizado prático de desenvolvimento de software e DevOps.

## Stack

| Camada | Tecnologia | Situação |
|---|---|---|
| Desktop | Python + PySide6 | Planejado |
| Backend | Python 3.12 + FastAPI + Uvicorn | Em desenvolvimento |
| Banco de dados | PostgreSQL 17 | Em uso no Docker Compose; o desenvolvimento sem Docker pode usar SQLite |
| Acesso ao banco | SQLAlchemy + psycopg | Em uso |
| Migrações | Alembic | Em uso |
| Hash de senhas | Argon2 (`argon2-cffi`) | Em uso |
| Testes | pytest + httpx | Em uso |
| Contêiner | Docker (imagem multi-stage) | Em uso |
| Orquestração local | Docker Compose | Em uso |
| Lint do Dockerfile | hadolint | Em uso |
| CI | GitHub Actions | Em uso |

## Estrutura do repositório

```text
.github/workflows/ci.yml   Pipeline de integração contínua
docker-compose.yml         Sobe a API, as migrações e o PostgreSQL
.env.example               Modelo das variáveis do Compose (só valores fictícios)
scripts/smoke-test.sh      Verifica se a API está no ar e gravando no banco
devops.md                  Práticas de DevOps usadas no projeto
backend/
  app/                     Código da API (rotas, serviços, repositórios, modelos)
  migrations/              Histórico de alterações do banco (Alembic)
  tests/                   Testes automatizados
  Dockerfile               Receita da imagem da API
  .dockerignore            Define o que pode entrar na imagem
  .env.example             Modelo das variáveis do backend sem Docker (só valores fictícios)
  requirements.txt         Dependências de produção
  requirements-dev.txt     Dependências de produção + testes
```

## Como executar

### Com Docker Compose (recomendado)

Requer o Docker em execução. Crie o `.env` na raiz do repositório e troque a senha:

```powershell
Copy-Item .env.example .env
```

Depois, suba tudo:

```powershell
docker compose up -d --build --wait
```

O Compose inicia os serviços nesta ordem:

1. **`db`:** o PostgreSQL. Os próximos serviços esperam o banco ficar saudável.
2. **`migrate`:** aplica as migrações e termina.
3. **`api`:** a API, em <http://127.0.0.1:8000/docs>.

Para conferir e administrar a stack:

| Comando | O que faz |
|---|---|
| `bash scripts/smoke-test.sh` | Testa a API e a gravação no banco (cria um usuário descartável) |
| `docker compose ps -a` | Mostra a situação dos serviços (`migrate` aparece como encerrado) |
| `docker compose logs -f api` | Acompanha os logs da API |
| `docker compose down` | Para a stack e mantém os dados |
| `docker compose down -v` | Para a stack e **apaga os dados do banco** |

### Sem Docker

Usa SQLite por padrão, o que basta para desenvolver a API:

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Testes

```powershell
cd backend
pytest
```

Os testes usam um SQLite em memória, então não precisam de um banco instalado. A aplicação ainda exige a `DATABASE_URL` para iniciar, por isso é preciso ter o `backend/.env` ou essa variável definida.

## Configuração

Os arquivos `.env` ficam fora do Git. Nunca coloque credenciais reais nos arquivos `.env.example`, no código, no `Dockerfile`, no `docker-compose.yml` ou neste README.

### Docker Compose (`.env` na raiz)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `POSTGRES_USER` | Sim | Usuário do banco |
| `POSTGRES_PASSWORD` | Sim | Senha do banco. Use só letras e números, porque ela também entra na URL de conexão |
| `POSTGRES_DB` | Sim | Nome do banco |
| `API_IMAGE` | Não | Imagem da API a executar. O padrão é `securevault-api:local` |

Sem as variáveis obrigatórias, o Compose para com um erro antes de iniciar qualquer serviço. A senha do banco só é definida quando o volume é criado pela primeira vez: para trocá-la depois, é preciso alterá-la dentro do PostgreSQL ou recriar o volume, o que apaga os dados.

### Backend sem Docker (`backend/.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Sim | URL de conexão com o banco, no formato do SQLAlchemy |

Sem essa variável, a aplicação não inicia. Para PostgreSQL, a URL precisa indicar o driver: `postgresql+psycopg://usuario:senha@host:5432/banco`.

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Informa se o processo da API está respondendo. Não verifica o banco |
| `POST` | `/auth/register` | Cadastra um usuário |

## Banco de dados

### Tabelas

| Tabela | Conteúdo |
|---|---|
| `users` | Usuários, com o hash da senha e o salt usado para derivar a chave de criptografia |
| `categories` | Categorias de credenciais de cada usuário |
| `credentials` | Credenciais de cada usuário, com os dados criptografados |
| `audit_logs` | Registro das ações sobre as credenciais |

### Migrações

O Alembic mantém o histórico de alterações do banco em `backend/migrations/versions/`. Para alterar uma tabela:

1. Altere o modelo em `backend/app/models/`.
2. Com o banco atualizado, gere a migração: `alembic revision --autogenerate -m "descreva a mudanca"`.
3. Revise o arquivo gerado, porque o gerador não cobre todos os casos.
4. Aplique com `alembic upgrade head`.

## Imagem Docker

A imagem da API foi montada com estas decisões:

| Decisão | Motivo |
|---|---|
| Build multi-stage | A instalação das dependências acontece em um estágio separado, e só o resultado vai para a imagem final |
| Base `python:3.12-slim` | Imagem enxuta, na mesma versão do Python usada no CI |
| Dependências de produção separadas | Ferramentas de teste não entram na imagem: são 26 pacotes de produção |
| Usuário sem privilégios (UID 1000) | Se a aplicação for invadida, o atacante não é root dentro do contêiner |
| `.dockerignore` como lista de permissão | Só o código, as migrações e o `requirements.txt` entram no build, então arquivos como `.env` ou bancos locais não vão para a imagem |
| Nenhum segredo na imagem | `DATABASE_URL` é informada ao rodar o contêiner e não fica gravada nas camadas |
| `HEALTHCHECK` em `/health` | O Docker sabe se a API está respondendo, não apenas se o processo existe |

A imagem final ocupa cerca de 312 MB, dos quais cerca de 180 MB são da imagem base.

## Docker Compose

| Decisão | Motivo |
|---|---|
| Banco sem porta publicada | Só os serviços da rede do Compose alcançam o PostgreSQL |
| API publicada só em `127.0.0.1` | A API fica acessível nesta máquina, não na rede local |
| Migrações em um serviço separado | A API só inicia depois que o banco está na versão certa |
| `depends_on` com condição | A ordem depende de o banco estar pronto, não apenas de o contêiner existir |
| Volume nomeado para o banco | Os dados sobrevivem quando os contêineres são recriados |
| API com sistema de arquivos somente leitura | Um invasor não consegue alterar o código nem gravar fora de `/tmp` |
| Sem capabilities do Linux e `no-new-privileges` | A API roda sem privilégios extras do sistema e não consegue obtê-los |
| Variáveis com `:?` | Falta de configuração interrompe a subida com uma mensagem clara |

## Pipeline de CI

O pipeline roda a cada push e pull request para a `main`:

1. **`test`:** instala as dependências e executa o `pytest`.
2. **`docker`:** roda somente se os testes passarem. Valida a stack completa em um ambiente descartável:
   1. Valida o `Dockerfile` com o hadolint.
   2. Gera a imagem e sobe a stack com o PostgreSQL, usando o `.env.example`.
   3. Confere se as migrações correspondem aos modelos (`alembic check`).
   4. Executa o `scripts/smoke-test.sh`.
   5. Em caso de falha, mostra os logs dos serviços.

## Limitações conhecidas

- Os testes automatizados rodam em SQLite. No PostgreSQL, o pipeline verifica as migrações e o fluxo do smoke test, mas não toda a suíte.
- `/health` não verifica o banco, então a API pode aparecer como saudável com o banco fora do ar.
- A senha do banco fica em variáveis de ambiente dos contêineres, visíveis para quem tem acesso ao Docker da máquina.

## Roteiro DevOps

| Fase | Entrega | Situação |
|---|---|---|
| A1 | Repositório, testes e pipeline de CI | Concluída |
| A2 | Dockerfile otimizado | Concluída |
| A2 | Orquestração com Docker Compose | Concluída |
| A2 | Pipeline de CD e deploy simulado | Pendente |
| A2 | Gestão de segredos no CI/CD | Em andamento |
| A2 | Versionamento semântico e rollback | Pendente |
| A3 | DevSecOps, observabilidade e demonstração | Pendente |
