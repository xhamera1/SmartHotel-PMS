"""Validate emitted datasets against pandera contracts; emit a JSON report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pandera.errors as pa_errors

from datagen.schemas import DATASET_SCHEMAS
from datagen.tables import DATASET_NAMES


class DatasetValidationError(Exception):
    """One or more parquet tables failed their pandera data contract."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        failed = [t.name for t in report.tables if t.status == "failed"]
        super().__init__(f"dataset validation failed for: {', '.join(failed)}")


@dataclass(frozen=True)
class TableValidation:
    name: str
    rows: int
    status: str
    errors: list[str]


@dataclass(frozen=True)
class ValidationReport:
    status: str
    tables: list[TableValidation]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "tables": {
                t.name: {
                    "rows": t.rows,
                    "status": t.status,
                    "errors": t.errors,
                }
                for t in self.tables
            },
        }

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _format_schema_errors(exc: BaseException) -> list[str]:
    if isinstance(exc, pa_errors.SchemaErrors):
        failure = exc.failure_cases
        if failure is None or getattr(failure, "empty", True):
            return [str(exc)]
        lines: list[str] = []
        for row in failure.head(20).itertuples(index=False):
            col = getattr(row, "column", None)
            check = getattr(row, "check", None)
            failure_case = getattr(row, "failure_case", None)
            lines.append(f"column={col} check={check} failure={failure_case}")
        if len(failure) > 20:
            lines.append(f"... and {len(failure) - 20} more")
        return lines
    return [str(exc)]


def validate_datasets(datasets: dict[str, pd.DataFrame]) -> ValidationReport:
    """
    Run pandera schemas on every table. Empty frames only check column names.

    Raises ``DatasetValidationError`` (with a full report) on any contract violation.
    """
    missing = [name for name in DATASET_NAMES if name not in datasets]
    if missing:
        raise KeyError(f"missing datasets: {missing}")

    tables: list[TableValidation] = []

    for name in DATASET_NAMES:
        frame = datasets[name]
        schema = DATASET_SCHEMAS[name]
        try:
            if len(frame) == 0:
                expected = set(schema.to_schema().columns)
                actual = set(frame.columns)
                if expected != actual:
                    raise ValueError(f"{name}: columns {sorted(actual)} != {sorted(expected)}")
                tables.append(TableValidation(name=name, rows=0, status="ok", errors=[]))
                continue

            schema.validate(frame, lazy=True)
            tables.append(TableValidation(name=name, rows=len(frame), status="ok", errors=[]))
        except (pa_errors.SchemaErrors, pa_errors.SchemaError, ValueError) as exc:
            tables.append(
                TableValidation(
                    name=name,
                    rows=len(frame),
                    status="failed",
                    errors=_format_schema_errors(exc),
                )
            )

    report = ValidationReport(
        status="passed" if all(t.status == "ok" for t in tables) else "failed",
        tables=tables,
    )
    if report.status != "passed":
        raise DatasetValidationError(report)
    return report
