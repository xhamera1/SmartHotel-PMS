# fixtures

Committed serving artifacts used by API tests and local compose when no active
`model_registry` row is present (`ALLOW_FIXTURE_MODEL=true`).

| Path | Role |
|------|------|
| `models/tiny/model.joblib` | Tiny Random Forest pipeline matching `FEATURE_SCHEMA_HASH` |
| `models/tiny/metadata.json` | Version, metrics, schema hash |
| `build_tiny_model.py` | Regenerates the fixture (`PYTHONPATH=. uv run python fixtures/build_tiny_model.py`) |
