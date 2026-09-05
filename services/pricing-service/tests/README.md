# tests

pytest suite: unit + property-based (hypothesis), API tests (httpx), DB integration
(testcontainers-python), contract fuzzing (schemathesis), golden prompt snapshots.
Committed tiny fixtures (dataset/model) live in `fixtures/`. External-API smoke tests
are marked `@pytest.mark.external` and excluded from CI.
