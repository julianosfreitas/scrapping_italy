#!/usr/bin/env bash
# Smoke test do deploy: confere que todas as páginas e endpoints públicos
# respondem. Uso:
#
#     ./deploy/smoke.sh                       # local (http://localhost:8000)
#     ./deploy/smoke.sh https://seu.dominio   # produção
#
# Sai com código 1 na primeira falha, para poder ser usado no pipeline.

set -uo pipefail

BASE="${1:-http://localhost:8000}"
FALHAS=0

verificar() {
  local caminho="$1" esperado="${2:-200}"
  local codigo
  codigo=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${BASE}${caminho}")
  if [ "$codigo" = "$esperado" ]; then
    printf '  ok   %-38s %s\n' "$caminho" "$codigo"
  else
    printf '  FALHA %-37s %s (esperado %s)\n' "$caminho" "$codigo" "$esperado"
    FALHAS=$((FALHAS + 1))
  fi
}

echo "Smoke test em ${BASE}"
echo "— saúde e documentação"
verificar /health
verificar /docs

echo "— páginas"
verificar /
verificar /estudantes
verificar /universidades
verificar /radar
verificar /newsletter
verificar /ajuda
verificar /login

echo "— api pública"
verificar /api/estudantes
verificar /api/noticias
verificar /api/universidades
verificar /api/faq
verificar /api/newsletter/edicoes

echo "— estáticos"
verificar /static/js/perfil.js

echo "— rotas privadas devem recusar sem token"
verificar /api/newsletter/inscritos 401

echo
if [ "$FALHAS" -eq 0 ]; then
  echo "Smoke test PASSOU."
  exit 0
fi
echo "Smoke test FALHOU: ${FALHAS} verificação(ões)."
exit 1
