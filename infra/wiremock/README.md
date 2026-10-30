# WireMock stubs (compose profile `stubs`)

Stub mappings for offline Ticketmaster Discovery and Gemini-shaped HTTP.

```powershell
docker compose --env-file .env -f infra/compose.yml --profile stubs up -d
# WireMock: http://localhost:8089
```

Point pricing at stubs when exercising Ticketmaster/Gemini clients without live keys
(adapter base URLs / env — prefer `EVENT_PROVIDER=static` for default demos).
