#!/usr/bin/env bash
# Exercício de rollback: simula uma release com defeito e volta para a versão estável.
# Uso: bash scripts/rollback-drill.sh <versão-estável>
# Exemplo: bash scripts/rollback-drill.sh 0.1.1
# As variáveis POSTGRES_* vêm do ambiente ou do arquivo .env.
# A imagem com defeito é gerada só nesta máquina e nunca vai para o registry.
set -euo pipefail

stable_version="$1"
repository="ghcr.io/lucasqueiroz10/securevault-api"
stable_image="${repository}:${stable_version}"
broken_version="${stable_version}-defeito"
broken_image="${repository}:${broken_version}"
base_url="http://127.0.0.1:8000"
username="drill_$(date +%s)_${RANDOM}"
payload="{\"username\":\"${username}\",\"password\":\"$(openssl rand -hex 16)\"}"

step() {
  echo
  echo "=== $1 ==="
}

register() {
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

step "1. Implantar a versão estável ${stable_version}"
bash scripts/deploy.sh "${stable_image}" "${stable_version}"

step "2. Gravar um dado antes da falha"
check "usuário de controle criado" 201 "$(register)"

step "3. Tentar implantar a versão com defeito ${broken_version}"
# Mesmo código da versão estável, mas o processo da API encerra ao iniciar.
docker build -q -t "${broken_image}" - <<EOF
FROM ${stable_image}
CMD ["python", "-c", "raise SystemExit('Falha simulada ao iniciar a API')"]
EOF

if bash scripts/deploy.sh "${broken_image}" "${broken_version}"; then
  echo "FALHOU: o deploy deveria ter recusado a versão com defeito"
  exit 1
fi
echo "OK: o deploy detectou o defeito e terminou com erro"
check "API fora do ar por causa do defeito" 000 "$(curl -s -m 5 -o /dev/null -w '%{http_code}' "${base_url}/health" || true)"

step "4. Rollback para a versão ${stable_version}"
started_at="$(date +%s)"
bash scripts/deploy.sh "${stable_image}" "${stable_version}"
echo "Tempo de rollback: $(( $(date +%s) - started_at )) s"

step "5. Verificar o resultado"
echo "/health: $(curl -s "${base_url}/health")"
check "usuário de controle preservado (cadastro repetido recusado)" 409 "$(register)"
docker image rm "${broken_image}" > /dev/null

echo
echo "Exercício concluído: rollback para ${stable_version} com os dados preservados"
