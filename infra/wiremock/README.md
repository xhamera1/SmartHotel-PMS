# wiremock

WireMock stub mappings for external dependencies (Ticketmaster Discovery API, Gemini)
used by the `stubs` compose profile. CI and E2E never call real external APIs (plan §5.1);
live calls happen only in the manual `live-smoke.yml` workflow.
