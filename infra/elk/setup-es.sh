#!/usr/bin/env bash
# Apply ILM + index template (dynamic:false). Run after Elasticsearch is healthy.
set -euo pipefail

ES_URL="${ES_URL:-http://127.0.0.1:9200}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Waiting for Elasticsearch at ${ES_URL}..."
for i in $(seq 1 60); do
  if curl -sf "${ES_URL}/_cluster/health" >/dev/null; then
    break
  fi
  sleep 2
done
curl -sf "${ES_URL}/_cluster/health" >/dev/null

echo "Putting ILM policy smarthotel-7d..."
curl -sf -X PUT "${ES_URL}/_ilm/policy/smarthotel-7d" \
  -H 'Content-Type: application/json' \
  --data-binary @"${ROOT}/ilm-policy.json" >/dev/null

echo "Putting index template smarthotel..."
curl -sf -X PUT "${ES_URL}/_index_template/smarthotel" \
  -H 'Content-Type: application/json' \
  --data-binary @"${ROOT}/index-template.json" >/dev/null

echo "ES observability setup OK."
