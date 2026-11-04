#!/usr/bin/env bash
# Verifica se a API está no ar e gravando no banco de verdade.
# Uso: bash scripts/smoke-test.sh [url-base]
# Cria um usuário descartável a cada execução.
set -euo pipefail

base_url="${1:-http://127.0.0.1:8000}"
username="smoke_$(date +%s)_${RANDOM}"
password="$(openssl rand -hex 16)"
payload="{\"username\":\"${username}\",\"password\":\"${password}\"}"

post_register() {
  curl -s -o /dev/null -w '%{http_code}' -X POST "${base_url}/auth/register" \
    -H 'Content-Type: application/json' -d "${payload}"
}

check() {
  if [ "$2" != "$3" ]; then
    echo "FALHOU: $1 (esperado $2, recebido $3)"
    exit 1
  fi
  echo "OK: $1"
}

check "API responde em /health" 200 "$(curl -s -o /dev/null -w '%{http_code}' "${base_url}/health")"
check "cadastro grava no banco" 201 "$(post_register)"
check "cadastro repetido encontra o registro gravado" 409 "$(post_register)"
