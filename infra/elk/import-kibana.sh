#!/usr/bin/env bash
# Create a proper Data View (with @timestamp) + import saved searches/dashboards.
# Hand-rolled index-pattern SO alone breaks Discover (isPersisted / missing time field).
set -euo pipefail

KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:5601}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
DV_ID="smarthotel-logs"

echo "Waiting for Kibana..."
for i in $(seq 1 60); do
  if curl -sf "${KIBANA_URL}/api/status" >/dev/null; then
    break
  fi
  sleep 3
done

echo "Upserting Data View ${DV_ID} (title=smarthotel-*, timeField=@timestamp)..."
# Delete stale / broken object if present
curl -sf -X DELETE "${KIBANA_URL}/api/data_views/data_view/${DV_ID}" \
  -H 'kbn-xsrf: true' >/dev/null 2>&1 || true

CREATE=$(curl -sf -X POST "${KIBANA_URL}/api/data_views/data_view" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d "{
    \"data_view\": {
      \"id\": \"${DV_ID}\",
      \"title\": \"smarthotel-*\",
      \"name\": \"SmartHotel logs\",
      \"timeFieldName\": \"@timestamp\",
      \"allowNoIndex\": true
    }
  }")
echo "${CREATE}" | head -c 400
echo

echo "Setting default data view..."
curl -sf -X POST "${KIBANA_URL}/api/data_views/default" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d "{\"data_view_id\":\"${DV_ID}\",\"force\":true}" >/dev/null || true

echo "Importing saved searches + dashboards (skipping index-pattern line)..."
# Drop the first ndjson line (legacy index-pattern) — Data View API owns that object now.
tail -n +2 "${ROOT}/kibana-saved-objects.ndjson" > /tmp/smarthotel-kibana-partial.ndjson
curl -sf -X POST "${KIBANA_URL}/api/saved_objects/_import?overwrite=true" \
  -H 'kbn-xsrf: true' \
  --form file=@/tmp/smarthotel-kibana-partial.ndjson

echo
echo "OK. Open Discover → data view \"SmartHotel logs\" / smarthotel-*"
echo "  ${KIBANA_URL}/app/discover"
echo "If Discover still errors: hard-refresh (Ctrl+Shift+R) or clear site data for localhost:5601."
