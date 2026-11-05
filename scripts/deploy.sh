#!/usr/bin/env bash
# Implanta uma versão publicada da API e confirma que ela está funcionando.
# Uso: bash scripts/deploy.sh <imagem> <versão>
# Exemplo: bash scripts/deploy.sh ghcr.io/lucasqueiroz10/securevault-api:0.1.1 0.1.1
# As variáveis POSTGRES_* vêm do ambiente ou do arquivo .env.
set -euo pipefail

export API_IMAGE="$1"
version="$2"

trap 'echo "FALHOU: deploy da versão ${version}"; docker compose logs' ERR

echo "Implantando ${API_IMAGE}"
# Uma imagem que falta em todo lugar ainda falha no "up" abaixo, antes de trocar os contêineres.
docker compose pull --ignore-pull-failures migrate api
# --no-build: se a imagem não vier do registry, o deploy falha em vez de gerar
# outra localmente, que não seria o artefato publicado.
docker compose up -d --no-build --wait --wait-timeout 120

bash scripts/smoke-test.sh "http://127.0.0.1:8000" "${version}"
echo "Versão ${version} implantada"
