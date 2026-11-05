# Versionamento e rollback

Este documento descreve como o SecureVault volta para uma versão anterior em caso de falha e registra a simulação desse fluxo.

## Estratégia

Rollback é um novo deploy de uma versão anterior e exata. Como cada release publica uma imagem identificada pela versão semântica e pelo digest, voltar não exige recompilar nem alterar código: basta implantar a versão desejada, usando o mesmo script e as mesmas verificações de um deploy comum.

As releases ficam em [Releases](https://github.com/LucasQueiroz10/securevault/releases), cada uma com a referência e o digest da imagem. A versão no ar é informada pelo endpoint `/health`.

## Quando fazer rollback

Faça rollback quando uma versão implantada falhar e a correção não for imediata. Exemplos:

- A API não fica saudável depois do deploy.
- O smoke test falha.
- Um defeito grave aparece depois do deploy.

## Procedimento

1. **Identifique a versão no ar**, consultando `/health`.
2. **Escolha a versão de destino:** a última estável, em [Releases](https://github.com/LucasQueiroz10/securevault/releases).
3. **Verifique se a versão com falha alterou o banco** (veja a seção seguinte).
4. **Implante a versão de destino:**
   ```bash
   bash scripts/deploy.sh ghcr.io/lucasqueiroz10/securevault-api:0.1.1 0.1.1
   ```
5. **Confira o resultado.** O próprio script executa o smoke test, que confere a versão no ar e a gravação no banco.
6. **Registre o que aconteceu** e corrija o defeito em uma nova versão. Uma tag publicada não é reaproveitada.

## Rollback e banco de dados

Voltar a imagem não desfaz alterações no banco. Cada deploy executa `alembic upgrade head`, e uma versão antiga não reconhece uma migração criada depois dela, então o serviço `migrate` falharia.

Se a versão com falha incluiu uma migração, há dois caminhos antes de implantar a versão anterior:

| Situação | O que fazer |
|---|---|
| A migração pode ser desfeita sem perda de dados | Execute `alembic downgrade` usando a imagem da versão com falha, que conhece a migração |
| Desfazer a migração apagaria dados | Prefira corrigir em uma nova versão ou restaurar um backup |

Para reduzir esse risco, as migrações devem ser compatíveis com a versão anterior sempre que possível: primeiro adicionar colunas e tabelas, e só remover o que ficou sem uso em uma release posterior.

As versões publicadas até agora compartilham a mesma migração inicial, então voltar entre elas não exige alterar o banco.

## Simulação

O exercício fica em [scripts/rollback-drill.sh](../scripts/rollback-drill.sh) e não usa dados reais.

| Passo | O que acontece | Resultado esperado |
|---|---|---|
| 1 | Implanta a versão estável, baixada do registry | Smoke test aprovado |
| 2 | Cadastra um usuário de controle | Resposta 201 |
| 3 | Tenta implantar uma imagem cujo processo encerra ao iniciar | O deploy termina com erro, e a API fica fora do ar |
| 4 | Executa o rollback para a versão estável | Smoke test aprovado, com a versão correta |
| 5 | Tenta cadastrar de novo o usuário de controle | Resposta 409, o que prova que o dado foi preservado |

A imagem com defeito é gerada apenas na máquina que executa o exercício e nunca é publicada.

### Como executar

**No GitHub Actions:** em **Actions → Rollback Drill → Run workflow**, informe a versão estável (por exemplo, `0.1.1`).

**Localmente:** com o Docker em execução e o `.env` da raiz criado:

```bash
bash scripts/rollback-drill.sh 0.1.1
```

Nesse caso, o exercício troca a versão da API na stack local e deixa os usuários de teste no banco dela.

### Resultado registrado

Execução local em 04/11/2026, com a imagem publicada `ghcr.io/lucasqueiroz10/securevault-api:0.1.1`. O exercício completo levou 32 s, e o rollback levou 8 s. Trecho da saída:

```text
=== 1. Implantar a versão estável 0.1.1 ===
Implantando ghcr.io/lucasqueiroz10/securevault-api:0.1.1
OK: API responde em /health
OK: versão no ar
OK: cadastro grava no banco
OK: cadastro repetido encontra o registro gravado
Versão 0.1.1 implantada

=== 2. Gravar um dado antes da falha ===
OK: usuário de controle criado

=== 3. Tentar implantar a versão com defeito 0.1.1-defeito ===
Implantando ghcr.io/lucasqueiroz10/securevault-api:0.1.1-defeito
FALHOU: deploy da versão 0.1.1-defeito
api-1      | Falha simulada ao iniciar a API
OK: o deploy detectou o defeito e terminou com erro
OK: API fora do ar por causa do defeito

=== 4. Rollback para a versão 0.1.1 ===
Tempo de rollback: 8 s

=== 5. Verificar o resultado ===
/health: {"status":"ok","version":"0.1.1"}
OK: usuário de controle preservado (cadastro repetido recusado)

Exercício concluído: rollback para 0.1.1 com os dados preservados
```

## Falhas reais durante a implantação do pipeline

Estas falhas ocorreram de verdade e foram contidas pelas verificações do fluxo. Nenhuma exigiu rollback, porque nenhuma versão com falha chegou a ser liberada.

### Secret ausente no deploy da v0.1.1

| | |
|---|---|
| **Sintoma** | O job `deploy` falhou com `required variable POSTGRES_PASSWORD is missing a value` |
| **Causa** | O secret ainda não havia sido criado no environment `homologacao` |
| **Impacto** | Nenhum: a imagem foi publicada, mas o job `release` foi pulado |
| **Correção** | Criar o secret e executar novamente os jobs que falharam, com a mesma imagem |
| **Horários (UTC, 05/11/2026)** | Primeiro deploy às 00:30, segundo às 00:35 e release às 00:36 |
| **Aprendizado** | A validação da configuração interrompeu o deploy antes de subir qualquer serviço. A mensagem de erro citava apenas o `.env` e foi ajustada para citar também o GitHub Secrets |

### Tag v0.1.0 em um commit sem o pipeline

| | |
|---|---|
| **Sintoma** | A tag foi enviada, mas o workflow de CD não iniciou |
| **Causa** | A tag foi criada a partir de uma `main` local desatualizada, em um commit anterior ao `cd.yml` |
| **Impacto** | Nenhum: nada foi publicado com essa tag |
| **Correção** | A tag foi removida, e a primeira release passou a ser a `v0.1.1` |
| **Aprendizado** | Criar tags apontando para `origin/main`, e não para a branch local |

## Limitações

- **Indisponibilidade:** o Docker Compose substitui o contêiner em vez de manter duas versões ao mesmo tempo, então a API fica fora do ar durante a troca.
- **Rollback manual:** o deploy detecta a falha, mas a volta para a versão anterior é iniciada por uma pessoa. Como o ambiente de homologação é temporário, não há uma versão anterior em execução para o pipeline restaurar.
- **Defeito simulado:** o exercício usa uma falha ao iniciar, que é fácil de detectar. Defeitos que não afetam o smoke test só seriam percebidos depois, por monitoramento, que faz parte da próxima fase do projeto.
