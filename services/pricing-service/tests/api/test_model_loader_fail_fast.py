"""Fail-fast behaviour when feature_schema_hash drifts (Phase 6)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services.model_loader import ModelSchemaMismatchError, load_active_model, load_fixture_model
from ml.features import FEATURE_SCHEMA_HASH


def test_load_active_model_raises_on_registry_schema_mismatch() -> None:
    engine = MagicMock()
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    conn.execute.return_value.mappings.return_value.first.return_value = {
        "version": "bad",
        "feature_schema_hash": "not-the-real-hash",
        "artifact_path": "/tmp/missing.joblib",
        "metrics": {},
        "trained_at": "2026-01-01T00:00:00Z",
    }

    with pytest.raises(ModelSchemaMismatchError, match="schema hash mismatch"):
        load_active_model(engine, allow_fixture=False)


def test_load_fixture_raises_on_schema_mismatch(tmp_path: Path) -> None:
    model = tmp_path / "model.joblib"
    meta = tmp_path / "metadata.json"
    model.write_bytes(b"not-a-real-joblib")
    meta.write_text(
        '{"version":"x","feature_schema_hash":"wrong","metrics":{},"trained_at":""}',
        encoding="utf-8",
    )
    with pytest.raises(ModelSchemaMismatchError):
        load_fixture_model(tmp_path)


def test_fixture_tiny_matches_current_schema() -> None:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "models" / "tiny"
    state = load_fixture_model(fixture)
    assert state is not None
    assert state.feature_schema_hash == FEATURE_SCHEMA_HASH
