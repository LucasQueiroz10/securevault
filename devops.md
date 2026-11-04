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
