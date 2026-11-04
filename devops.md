# Práticas de DevOps do SecureVault

Este documento explica as práticas de DevOps aplicadas no projeto, o motivo de cada uma e onde encontrá-las no repositório. Para saber como executar a aplicação, consulte o [README](README.md).

## Containerização e pipeline da imagem

### Imagem imutável

O CI gera uma imagem única, que passa sem alterações por homologação e produção. Entre um ambiente e outro, muda apenas a configuração. Assim, o que foi testado é exatamente o que vai para produção, e o problema do "na minha máquina funciona" deixa de existir.

**No projeto:** a imagem é gerada a partir do [Dockerfile](backend/Dockerfile), e a configuração é informada ao iniciar o contêiner.

### Multi-stage build

A instalação das dependências acontece em um estágio descartável, e só o resultado vai para a imagem final. O que foi usado apenas durante o build fica de fora.

Hoje o ganho é pequeno, porque a aplicação não precisa de compilador, mas a estrutura já está pronta caso isso mude. O ganho concreto veio de não instalar o `pip` no ambiente virtual da aplicação, o que reduziu a imagem de 255 MB para 237 MB.

**No projeto:** os estágios `builder` e `runtime` do [Dockerfile](backend/Dockerfile).

### Cache de camadas

O Docker reaproveita cada passo do build até encontrar o primeiro que mudou, e refaz tudo a partir dele. Por isso, a ordem das instruções importa: o que muda pouco deve vir antes do que muda muito.

**No projeto:** o `requirements.txt` é copiado antes do código, então alterar o código não reinstala as dependências.

### Separação entre produção e desenvolvimento

Cada pacote na imagem representa mais peso e mais uma possível vulnerabilidade. Ferramentas de teste não têm utilidade em produção, então ficam de fora. Isso também reduz o que os scans de segurança precisam analisar.

**No projeto:** o [requirements.txt](backend/requirements.txt) tem os 21 pacotes de produção, e o [requirements-dev.txt](backend/requirements-dev.txt) acrescenta os de teste.

### Menor privilégio

Um processo deve ter apenas as permissões de que precisa. Se a API for invadida, um atacante sem acesso de root fica mais limitado dentro do contêiner.

O usuário é definido pelo número (UID), e não pelo nome, porque o Kubernetes só consegue verificar que um contêiner não roda como root a partir do número.

**No projeto:** a instrução `USER 1000:1000` do [Dockerfile](backend/Dockerfile).

## Segredos e configuração

### Segredos fora da imagem

As camadas de uma imagem ficam registradas e podem ser baixadas por quem tiver acesso ao registry. Um segredo gravado em uma camada continua recuperável mesmo que uma camada seguinte o apague. Por isso, credenciais só devem entrar quando o contêiner é iniciado.

**No projeto:** a `DATABASE_URL` não tem valor definido no [Dockerfile](backend/Dockerfile) e é informada ao rodar o contêiner.

### Lista de permissão no `.dockerignore`

Uma lista de bloqueio só protege contra o que alguém lembrou de listar. A lista de permissão faz o contrário: ignora tudo e libera apenas o necessário. Assim, um arquivo sensível novo fica de fora mesmo que ninguém se lembre dele.

**No projeto:** o [.dockerignore](backend/.dockerignore) libera apenas `app/` e `requirements.txt`.

### Fail fast

Se falta uma configuração obrigatória, a aplicação deve parar logo ao iniciar, com um erro claro. Isso é melhor do que subir aparentemente normal e falhar depois, quando a causa é mais difícil de identificar.

**No projeto:** a `DATABASE_URL` não tem valor padrão no [config.py](backend/app/core/config.py), então a aplicação não inicia sem ela.

## Verificação

### Healthcheck

Um processo pode continuar existindo com a API travada, então verificar apenas o processo não basta. O healthcheck pergunta à própria API se ela está respondendo. O deploy e o rollback automáticos dependem dessa informação para saber se uma versão nova está funcionando.

**No projeto:** o endpoint `/health` em [main.py](backend/app/main.py) e a instrução `HEALTHCHECK` do [Dockerfile](backend/Dockerfile).

### Lint e smoke test no pipeline

Cada verificação cobre uma etapa diferente:

| Verificação | O que garante |
|---|---|
| Lint do Dockerfile | Encontra problemas no `Dockerfile` antes do build |
| Build da imagem | Prova que a imagem pode ser gerada |
| Smoke test | Prova que a imagem gerada realmente sobe e responde |

A versão do hadolint, a ferramenta de lint, é fixada para que o resultado do pipeline não mude sozinho quando sair uma versão nova.

**No projeto:** o job `docker` do [ci.yml](.github/workflows/ci.yml).

## Orquestração e banco de dados

### Infraestrutura como código

Toda a infraestrutura necessária para rodar o projeto fica descrita em arquivos versionados, e não em passos manuais. Qualquer pessoa do grupo sobe o mesmo ambiente com um único comando, e cada mudança na infraestrutura passa por revisão e fica no histórico do Git.

**No projeto:** o [docker-compose.yml](docker-compose.yml) define a API, as migrações e o PostgreSQL.

### Ordem de inicialização baseada em saúde

Um contêiner iniciado não é um serviço pronto: o PostgreSQL leva alguns segundos para aceitar conexões. Se a API dependesse apenas de o contêiner existir, ela poderia falhar ao tentar usar um banco ainda indisponível. Por isso, cada serviço espera uma condição real.

**No projeto:** o `migrate` espera o `db` ficar saudável, e a `api` espera o `migrate` terminar com sucesso.

### Migrações versionadas

As alterações do banco ficam registradas em arquivos, assim como o código. Dessa forma, todo ambiente chega ao mesmo esquema pelo mesmo caminho, e cada alteração pode ser revisada.

A migração roda em um serviço separado, que termina ao concluir. Assim, a API não sobe com o banco desatualizado, e um erro de migração aparece antes de a versão nova receber tráfego.

Migrações geradas automaticamente precisam de revisão. Neste projeto, a revisão encontrou dois problemas: um valor padrão que só funcionava no PostgreSQL e um tipo enum que não era removido no `downgrade`, o que impediria reaplicar a migração.

**No projeto:** os arquivos em [backend/migrations/versions](backend/migrations/versions).

### Contêineres descartáveis, dados persistentes

Contêineres devem poder ser destruídos e recriados a qualquer momento, inclusive em uma atualização de versão. Os dados ficam fora deles, em um volume com ciclo de vida próprio.

**No projeto:** o volume `db-data`. O comando `docker compose down` preserva os dados, e `docker compose down -v` os apaga.

### Redução da superfície de ataque

Só deve ficar exposto o que precisa estar exposto, e cada camada limita o estrago caso a anterior falhe. Essa abordagem é chamada de defesa em profundidade.

| Medida | O que limita |
|---|---|
| Banco sem porta publicada | Ninguém fora da rede do Compose alcança o PostgreSQL |
| API publicada só em `127.0.0.1` | A rede local não alcança a API |
| Sistema de arquivos somente leitura | Um invasor não altera o código nem grava fora de `/tmp` |
| `cap_drop: ALL` | O processo não tem privilégios extras do Linux |
| `no-new-privileges` | O processo não consegue obter privilégios depois de iniciar |

**No projeto:** o bloco `x-api` e o serviço `db` do [docker-compose.yml](docker-compose.yml).

### Modelo versionado, segredo fora do Git

O `.env.example` documenta quais variáveis existem e fica no Git, apenas com valores fictícios. O `.env` real, com as senhas, nunca é versionado. Um segredo que entra no histórico do Git deve ser considerado vazado, mesmo que o commit seja apagado depois.

**No projeto:** o [.env.example](.env.example) e a regra do [.gitignore](.gitignore).

## Testes de integração no pipeline

### Ambiente efêmero

O pipeline sobe a stack inteira do zero a cada execução e a descarta no fim. Como nada sobrevive entre as execuções, um passo manual esquecido ou um resíduo de teste anterior não consegue esconder um problema.

**No projeto:** o passo `Start stack` do job `docker` no [ci.yml](.github/workflows/ci.yml). Ele usa o próprio `.env.example`, o que também prova que o modelo funciona.

### Detecção de divergência

Divergência (*drift*) é quando duas coisas que deveriam estar iguais deixam de estar, como os modelos do código e o esquema do banco. O `alembic check` compara os dois e falha se alguém alterou um modelo sem criar a migração.

**No projeto:** o passo `Check migrations match models` do [ci.yml](.github/workflows/ci.yml).

### Smoke test reaproveitável

O smoke test é um teste curto que confirma se o essencial funciona. Ele fica em um script, e não dentro do pipeline, para que a mesma verificação rode na máquina do desenvolvedor, no CI e depois de um deploy.

Neste projeto, o script cadastra um usuário e tenta cadastrá-lo de novo. O segundo pedido precisa ser recusado, o que prova que o primeiro foi realmente gravado no banco.

**No projeto:** o [scripts/smoke-test.sh](scripts/smoke-test.sh).
