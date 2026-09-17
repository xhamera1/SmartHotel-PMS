"""Tests for the CI metric-regression gate."""

from __future__ import annotations

import json

import pytest

from ml.features import FEATURE_SCHEMA_HASH
from ml.gate import MetricRegressionError, compare_to_baseline, run_gate


def _payload(multiplier_mae: float, price_mae: float) -> dict[str, object]:
    return {
        "protocol_version": 1,
        "protocol": {"random_state": 42},
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "metrics": {
            "multiplier_mae": multiplier_mae,
            "price_pln_mae": price_mae,
        },
    }


def test_gate_allows_exact_ten_percent_regression() -> None:
    report = compare_to_baseline(_payload(0.11, 55.0), _payload(0.1, 50.0))
    assert report["passed"] is True


def test_gate_rejects_regression_above_tolerance() -> None:
    report = compare_to_baseline(_payload(0.111, 50.0), _payload(0.1, 50.0))
    assert report["passed"] is False
    assert report["comparisons"]["multiplier_mae"]["passed"] is False


def test_gate_rejects_schema_mismatch() -> None:
    baseline = _payload(0.1, 50.0)
    baseline["feature_schema_hash"] = "old"
    with pytest.raises(ValueError, match="feature_schema_hash"):
        compare_to_baseline(_payload(0.1, 50.0), baseline)


def test_gate_rejects_protocol_mismatch() -> None:
    baseline = _payload(0.1, 50.0)
    baseline["protocol"] = {"random_state": 7}
    with pytest.raises(ValueError, match="protocols differ"):
        compare_to_baseline(_payload(0.1, 50.0), baseline)


def test_run_gate_persists_failure_evidence(tmp_path, monkeypatch) -> None:
    baseline_path = tmp_path / "baseline_metrics.json"
    baseline_path.write_text(json.dumps(_payload(0.1, 50.0)), encoding="utf-8")
    monkeypatch.setattr("ml.gate.quick_train_metrics", lambda _path: _payload(0.2, 100.0))
    output = tmp_path / "gate"

    with pytest.raises(MetricRegressionError):
        run_gate(
            dataset_path=tmp_path / "unused.parquet",
            baseline_path=baseline_path,
            output_dir=output,
        )

    assert (output / "quick_metrics.json").is_file()
    report = json.loads((output / "gate_report.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
