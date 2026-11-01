"""Tests for transactional model registry operations."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.exc import SQLAlchemyError

from ml.features import FEATURE_SCHEMA_HASH
from ml.registry import main, promote_model, register_artifact


class _Result:
    def __init__(self, scalar: object) -> None:
        self.scalar = scalar

    def scalar_one_or_none(self) -> object:
        return self.scalar


class _Connection:
    def __init__(self, *, exists: bool = True) -> None:
        self.exists = exists
        self.calls: list[tuple[str, object]] = []

    def execute(self, statement, values=None) -> _Result:
        sql = str(statement)
        self.calls.append((sql, values))
        return _Result(1 if self.exists and sql.lstrip().startswith("SELECT") else None)


class _Transaction:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    def __enter__(self) -> _Connection:
        return self.connection

    def __exit__(self, *_args) -> None:
        return None


class _Engine:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection
        self.disposed = False

    def begin(self) -> _Transaction:
        return _Transaction(self.connection)

    def dispose(self) -> None:
        self.disposed = True


def _metadata(tmp_path) -> object:
    path = tmp_path / "metadata.json"
    path.write_text(
        json.dumps(
            {
                "version": "rf-v1",
                "algorithm": "RandomForestRegressor",
                "artifact_path": "artifacts/models/rf-v1/model.joblib",
                "dataset_hash": "d" * 64,
                "config": {"random_state": 42},
                "metrics": {"mae": 0.1},
                "feature_schema_hash": FEATURE_SCHEMA_HASH,
                "git_sha": "a" * 40,
                "trained_at": "2026-09-17T12:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_register_inserts_inactive_artifact(tmp_path, monkeypatch) -> None:
    connection = _Connection()
    engine = _Engine(connection)
    monkeypatch.setattr("ml.registry.sa.create_engine", lambda _url: engine)

    register_artifact("postgresql://test", _metadata(tmp_path))

    sql, values = connection.calls[0]
    assert "INSERT INTO pricing.model_registry" in sql
    assert "false" in sql
    assert values["version"] == "rf-v1"
    assert engine.disposed is True


def test_promotion_deactivates_then_activates_in_one_transaction(monkeypatch) -> None:
    connection = _Connection()
    engine = _Engine(connection)
    monkeypatch.setattr("ml.registry.sa.create_engine", lambda _url: engine)

    promote_model("postgresql://test", "rf-v2")

    statements = [sql for sql, _values in connection.calls]
    assert statements[0].lstrip().startswith("SELECT")
    assert "SET is_active = false" in statements[1]
    assert "SET is_active = true" in statements[2]


def test_promotion_rejects_unknown_version(monkeypatch) -> None:
    connection = _Connection(exists=False)
    engine = _Engine(connection)
    monkeypatch.setattr("ml.registry.sa.create_engine", lambda _url: engine)

    with pytest.raises(ValueError, match="not found"):
        promote_model("postgresql://test", "missing")


def test_cli_reports_missing_metadata_without_traceback(tmp_path, capsys) -> None:
    missing = tmp_path / "missing-metadata.json"

    result = main(["register", "--metadata", str(missing), "--database-url", "postgresql://test"])

    captured = capsys.readouterr()
    assert result == 1
    assert "registry_error=" in captured.out
    assert missing.name in captured.out
    assert captured.err == ""


def test_cli_reports_database_error_without_traceback(monkeypatch, capsys) -> None:
    def fail_to_connect(_url):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr("ml.registry.sa.create_engine", fail_to_connect)

    result = main(["promote", "--version", "rf-v1", "--database-url", "postgresql://test"])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out.strip() == "registry_error=database unavailable"
    assert captured.err == ""
