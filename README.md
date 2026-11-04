# SecureVault

Cofre de senhas full stack (desktop + API), desenvolvido como projeto de aprendizado prático de desenvolvimento de software e DevOps.

## Stack

| Camada | Tecnologia | Situação |
|---|---|---|
| Desktop | Python + PySide6 | Planejado |
| Backend | Python 3.12 + FastAPI + Uvicorn | Em desenvolvimento |
| Persistência | SQLAlchemy + PostgreSQL | SQLAlchemy em uso; PostgreSQL planejado (hoje o desenvolvimento usa SQLite) |
| Hash de senhas | Argon2 (`argon2-cffi`) | Em uso |
| Testes | pytest + httpx | Em uso |
| Contêiner | Docker (imagem multi-stage) | Em uso |
| Lint do Dockerfile | hadolint | Em uso |
| CI | GitHub Actions | Em uso |

## Estrutura do repositório

```text
.github/workflows/ci.yml   Pipeline de integração contínua
backend/
  app/                     Código da API (rotas, serviços, repositórios, modelos)
  tests/                   Testes automatizados
  Dockerfile               Receita da imagem da API
  .dockerignore            Define o que pode entrar na imagem
  .env.example             Modelo das variáveis de ambiente (só valores fictícios)
  requirements.txt         Dependências de produção
  requirements-dev.txt     Dependências de produção + testes
```

## Configuração

A aplicação lê a configuração de variáveis de ambiente ou de um arquivo `backend/.env`, que fica fora do Git. Sem as variáveis obrigatórias, ela não inicia.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Sim | URL de conexão com o banco, no formato do SQLAlchemy |

Para criar o seu `.env` a partir do modelo:

```powershell
cd backend
Copy-Item .env.example .env
```

Nunca coloque credenciais reais no `.env.example`, no código, no `Dockerfile` ou neste README.

## Como executar

### Localmente

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

A documentação interativa da API fica em <http://localhost:8000/docs>.

### Com Docker

```powershell
docker build -t securevault-api:local backend
docker run --rm -p 8000:8000 -e DATABASE_URL=sqlite:////tmp/securevault.db securevault-api:local
```

Esse banco SQLite é temporário e some junto com o contêiner.

### Testes

```powershell
cd backend
pytest
```

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Informa se a API está no ar |
| `POST` | `/auth/register` | Cadastra um usuário |

## Imagem Docker

A imagem da API foi montada com estas decisões:

| Decisão | Motivo |
|---|---|
| Build multi-stage | A instalação das dependências acontece em um estágio separado, e só o resultado vai para a imagem final |
| Base `python:3.12-slim` | Imagem enxuta, na mesma versão do Python usada no CI |
| Dependências de produção separadas | Ferramentas de teste não entram na imagem: são 21 pacotes de produção |
| Usuário sem privilégios (UID 1000) | Se a aplicação for invadida, o atacante não é root dentro do contêiner |
| `.dockerignore` como lista de permissão | Só `app/` e `requirements.txt` entram no build, então arquivos como `.env` ou bancos locais não vão para a imagem |
| Nenhum segredo na imagem | `DATABASE_URL` é informada ao rodar o contêiner e não fica gravada nas camadas |
| `HEALTHCHECK` em `/health` | O Docker sabe se a API está respondendo, não apenas se o processo existe |

A imagem final ocupa cerca de 237 MB, dos quais cerca de 180 MB são da imagem base.

## Pipeline de CI

O pipeline roda a cada push e pull request para a `main`:

1. **`test`:** instala as dependências e executa o `pytest`.
2. **`docker`:** roda somente se os testes passarem. Valida o `Dockerfile` com o hadolint, gera a imagem, sobe um contêiner e aguarda o `HEALTHCHECK` aprovar.

## Limitações conhecidas

- As tabelas do banco ainda não são criadas fora dos testes. Por isso, `POST /auth/register` retorna erro 500 em uma instalação nova.

## Roteiro DevOps

| Fase | Entrega | Situação |
|---|---|---|
| A1 | Repositório, testes e pipeline de CI | Concluída |
| A2 | Dockerfile otimizado | Concluída |
| A2 | Orquestração com Docker Compose | Pendente |
| A2 | Pipeline de CD e deploy simulado | Pendente |
| A2 | Gestão de segredos no CI/CD | Em andamento |
| A2 | Versionamento semântico e rollback | Pendente |
| A3 | DevSecOps, observabilidade e demonstração | Pendente |
