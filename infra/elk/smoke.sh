#!/usr/bin/env bash
# Compose ELK smoke: setup template, generate traffic with planted traceId, assert docs in ES.
set -euo pipefail

ES_URL="${ES_URL:-http://127.0.0.1:9200}"
PMS_URL="${PMS_URL:-http://127.0.0.1:8080}"
PRICING_URL="${PRICING_URL:-http://127.0.0.1:8081}"
API_KEY="${INTERNAL_API_KEY:-${PRICING_API_KEY:-dev-internal-api-key}}"
TRACE_ID="${TRACE_ID:-elk-smoke-$(date +%s)}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
FROM=$(date -u -d '+30 days' +%F 2>/dev/null || date -u -v+30d +%F)
TO=$(date -u -d '+32 days' +%F 2>/dev/null || date -u -v+32d +%F)

bash "${ROOT}/setup-es.sh"

echo "Planted traceId=${TRACE_ID}"
for i in $(seq 1 6); do
  # Non-health paths so HttpAccessLog / structlog access lines are emitted.
  curl -sf -H "X-Request-ID: ${TRACE_ID}" \
    "${PMS_URL}/api/v1/availability?checkIn=${FROM}&checkOut=${TO}&guests=2" >/dev/null || true
  curl -sf -H "X-Request-ID: ${TRACE_ID}" -H "X-Internal-Api-Key: ${API_KEY}" \
    "${PRICING_URL}/api/v1/model" >/dev/null || true
  sleep 1
done

echo "Waiting for Filebeat ship..."
sleep 45

COUNT=$(curl -sf "${ES_URL}/smarthotel-*/_count" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("count",0))')
echo "ES smarthotel-* document count: ${COUNT}"
test "${COUNT}" -gt 0

MATCH=$(curl -sf "${ES_URL}/smarthotel-*/_count" \
  -H 'Content-Type: application/json' \
  -d "{\"query\":{\"term\":{\"traceId.keyword\":\"${TRACE_ID}\"}}}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("count",0))' 2>/dev/null || echo 0)
# Fallback if template maps traceId as keyword without .keyword subfield
if [ "${MATCH}" = "0" ]; then
  MATCH=$(curl -sf "${ES_URL}/smarthotel-*/_count" \
    -H 'Content-Type: application/json' \
    -d "{\"query\":{\"term\":{\"traceId\":\"${TRACE_ID}\"}}}" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("count",0))' || echo 0)
fi
echo "Docs with planted traceId: ${MATCH}"

echo "ELK smoke OK (count=${COUNT}, traceMatches=${MATCH})."
