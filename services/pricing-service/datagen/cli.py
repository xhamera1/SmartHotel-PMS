"""CLI entry: `python -m datagen run|eda ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datagen.config import DatagenConfig
from datagen.pipeline import run_generation
from datagen.validate import DatasetValidationError

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = PACKAGE_ROOT / "configs" / "default.yaml"
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "datasets" / "default"
DEFAULT_FIGURES = REPO_ROOT / "artifacts" / "eda" / "default"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datagen",
        description=(
            "SmartHotel synthetic dataset generator. "
            "Validates Appendix C YAML, seeds RNGs, writes parquet + metadata.json, "
            "and enforces pandera data contracts."
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

    eda = sub.add_parser("eda", help="Render Phase-4 EDA figures from an existing dataset")
    eda.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Config used for room capacities (default: default.yaml)",
    )
    eda.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Dataset directory with parquet files (default: {DEFAULT_OUTPUT})",
    )
    eda.add_argument(
        "--figures",
        type=Path,
        default=DEFAULT_FIGURES,
        help=f"Directory for PNG figures (default: {DEFAULT_FIGURES})",
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
        try:
            result = run_generation(
                config=config,
                config_path=config_path,
                output_dir=args.output,
            )
        except DatasetValidationError as exc:
            print(f"validation_failed={exc}", file=sys.stderr)
            for table in exc.report.tables:
                if table.status == "failed":
                    print(f"  {table.name}: {table.errors}", file=sys.stderr)
            return 1
        print(f"config_hash={result.config_hash}")
        print(f"seed={config.seed}")
        print(f"output={result.output_dir}")
        for name, count in result.row_counts.items():
            print(f"rows.{name}={count}")
        print(f"validation={result.validation.status}")
        print(f"validation_report={result.validation_path}")
        print(f"metadata={result.metadata_path}")
        return 0

    if args.command == "eda":
        from datagen.eda import run_eda

        config_path = args.config
        if not config_path.is_file():
            parser.error(f"config not found: {config_path}")
        if not args.input.is_dir():
            parser.error(f"dataset directory not found: {args.input}")
        config = DatagenConfig.from_yaml(config_path)
        rooms = {rt.code: rt.rooms for rt in config.hotel.room_types}
        result = run_eda(dataset_dir=args.input, figures_dir=args.figures, rooms_by_type=rooms)
        print(f"figures={result.figures_dir}")
        print(f"occupancy_mean={result.occupancy_mean:.4f}")
        for name, path in result.figure_paths.items():
            print(f"figure.{name}={path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
