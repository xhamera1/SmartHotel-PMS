# Observability (compose profile `observability`)

Single-node Elasticsearch (1g heap) + Kibana + Filebeat Docker autodiscover.

```powershell
docker compose --env-file .env -f infra/compose.yml --profile observability up -d
# Kibana: http://localhost:5601
# Elasticsearch: http://localhost:9200
```

`filebeat.yml` ships JSON container logs into index pattern `smarthotel-*`.
Keep this profile off during light local development (RAM).
