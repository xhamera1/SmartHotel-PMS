# infra

Runtime infrastructure:

- `compose.yml` — Docker Compose with profiles `core` (postgres only), `app` (full stack),
  `stubs` (WireMock for external APIs), `observability` (ELK). Lands in Phase 0, step 4.
- `elk/` — Filebeat config + exported Kibana saved objects (Phase 10).
- `wiremock/` — stub mappings for Ticketmaster/Gemini used by tests, CI, and offline demo.
- `seed/` — demo-narrative and performance data seeding (Phases 11, 14).
