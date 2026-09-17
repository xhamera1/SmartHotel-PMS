"""CLI entry: `python -m datagen run --config ... --output ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datagen.config import DatagenConfig
from datagen.pipeline import run_generation

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = PACKAGE_ROOT / "configs" / "default.yaml"
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "datasets" / "default"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datagen",
        description=(
            "SmartHotel synthetic dataset generator. "
            "Validates Appendix C YAML, seeds RNGs, writes parquet + metadata.json."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Generate dataset artifacts from a config file")
    run.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config (default: {DEFAULT_CONFIG})",
    )
    run.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory under artifacts/datasets/ (default: {DEFAULT_OUTPUT})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        config_path: Path = args.config
        if not config_path.is_file():
            parser.error(f"config not found: {config_path}")
        config = DatagenConfig.from_yaml(config_path)
        result = run_generation(
            config=config,
            config_path=config_path,
            output_dir=args.output,
        )
        print(f"config_hash={result.config_hash}")
        print(f"seed={config.seed}")
        print(f"output={result.output_dir}")
        for name, count in result.row_counts.items():
            print(f"rows.{name}={count}")
        print(f"metadata={result.metadata_path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
