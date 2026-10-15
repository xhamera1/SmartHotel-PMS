"""Export OpenAPI JSON for CI drift checks (D19)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import create_app
from app.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = REPO_ROOT / "docs" / "api" / "pricing-openapi.json"


def export_openapi(path: Path = DEFAULT_OUT) -> Path:
    # Export without connecting to a real DB during schema generation.
    settings = Settings(
        PRICING_DATABASE_URL="postgresql+psycopg://pricing_user:x@localhost:5432/smarthotel",
        INTERNAL_API_KEY="export-key",
        ALLOW_FIXTURE_MODEL=False,
    )
    application = create_app(settings)
    schema = application.openapi()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    out = Path(argv[0]) if argv else DEFAULT_OUT
    written = export_openapi(out)
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
