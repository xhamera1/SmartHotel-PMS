"""Golden datagen snapshot test (Phase 4).

Runs the tiny config and verifies the output matches a committed golden
hash. Any change to generator logic causes a diff that must be explicitly
reviewed and the golden hash updated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from datagen.cli import main

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"
GOLDEN_HASHES_FILE = Path(__file__).resolve().parent / "golden_hashes.json"

# These are the column-sorted, seed-stable SHA-256 hashes of the tiny-config
# output parquet files. Update them (by running this test with --update-golden)
# whenever the generator changes intentionally.
#
# To regenerate:
#   cd services/pricing-service
#   uv run pytest tests/datagen/test_golden_snapshot.py --update-golden -s


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_golden_hashes() -> dict[str, str]:
    if not GOLDEN_HASHES_FILE.exists():
        return {}
    return json.loads(GOLDEN_HASHES_FILE.read_text(encoding="utf-8"))


def _save_golden_hashes(hashes: dict[str, str]) -> None:
    GOLDEN_HASHES_FILE.write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_golden_datagen_snapshot(tmp_path: Path, request: pytest.FixtureRequest) -> None:
    """The tiny-config output must match the committed golden hashes.

    Run with ``--update-golden`` to regenerate the hashes file after an
    intentional generator change.
    """
    output = tmp_path / "golden"
    rc = main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)])
    assert rc == 0, "datagen CLI failed"

    parquets = sorted(output.glob("*.parquet"))
    assert len(parquets) >= 1, "No parquet files generated"

    current_hashes = {p.name: _hash_file(p) for p in parquets}
    # Also hash the metadata (minus the timestamp and absolute path)
    metadata_path = output / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    current_hashes["config_hash"] = metadata["config_hash"]

    update_mode = request.config.getoption("--update-golden", default=False)
    if update_mode:
        _save_golden_hashes(current_hashes)
        pytest.skip("Golden hashes updated — commit the new golden_hashes.json")

    golden = _load_golden_hashes()
    if not golden:
        _save_golden_hashes(current_hashes)
        pytest.skip(
            "No golden hashes found — created initial golden_hashes.json. "
            "Commit it and re-run."
        )

    for name, expected_hash in golden.items():
        actual = current_hashes.get(name)
        assert actual is not None, f"Missing output: {name}"
        assert actual == expected_hash, (
            f"Golden snapshot mismatch for {name}:\n"
            f"  expected: {expected_hash}\n"
            f"  actual:   {actual}\n"
            "If this is intentional, re-run with: "
            "pytest tests/datagen/test_golden_snapshot.py --update-golden"
        )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate golden datagen hashes",
    )
