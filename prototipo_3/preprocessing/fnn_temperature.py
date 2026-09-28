"""Run a reproducible False Nearest Neighbors diagnostic on a temperature CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from nolitsa import dimension

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_series(path: Path, column: str) -> tuple[list[tuple[datetime, float | None]], int]:
    series: list[tuple[datetime, float | None]] = []
    missing = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            timestamp = datetime.fromisoformat(row["timestamp_utc"]).astimezone(UTC)
            raw = row[column].strip()
            if raw == "":
                missing += 1
                series.append((timestamp, None))
            else:
                series.append((timestamp, float(raw)))
    return series, missing


def contiguous_segments(series: list[tuple[datetime, float | None]]) -> list[list[float]]:
    """Split at missing observations and at any non-hourly timestamp gap."""
    segments: list[list[float]] = []
    current: list[float] = []
    previous: datetime | None = None
    for timestamp, value in series:
        if value is None or (previous is not None and timestamp - previous != timedelta(hours=1)):
            if current:
                segments.append(current)
            current = []
            previous = None
            if value is None:
                continue
        current.append(value)
        previous = timestamp
    if current:
        segments.append(current)
    return segments


def first_below(values: np.ndarray, threshold: float) -> int | None:
    for index, value in enumerate(values):
        if np.isfinite(value) and value <= threshold:
            return index + 1
    return None


def run_fnn(values: list[float], dimensions: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    result = dimension.fnn(
        np.asarray(values, dtype=float),
        dim=dimensions,
        tau=args.tau,
        R=args.R,
        A=args.A,
        window=args.window,
        maxnum=args.maxnum,
        parallel=False,
    )
    if result.shape != (3, len(dimensions)):
        raise ValueError(f"Unexpected Nolitsa output shape: {result.shape}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Hourly temperature CSV")
    parser.add_argument("--column", default="temperature_C")
    parser.add_argument("--tau", type=int, default=1, help="Embedding delay in samples/hours")
    parser.add_argument("--max-dim", type=int, default=15)
    parser.add_argument("--R", type=float, default=10.0, help="FNN Test I tolerance")
    parser.add_argument("--A", type=float, default=2.0, help="FNN Test II tolerance")
    parser.add_argument("--window", type=int, default=10, help="Theiler temporal window")
    parser.add_argument("--maxnum", type=int, default=100, help="Maximum neighbor candidates for duplicate values")
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "corfo-report/validation/berlin/fnn_temperature_2023.csv",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO / "corfo-report/validation/berlin/fnn_temperature_2023.json",
    )
    args = parser.parse_args()
    source = args.input.resolve()
    output = args.output if args.output.is_absolute() else REPO / args.output
    manifest_path = args.manifest if args.manifest.is_absolute() else REPO / args.manifest
    series, missing = read_series(source, args.column)
    segments = contiguous_segments(series)
    min_length = args.max_dim * args.tau + 100
    usable = [segment for segment in segments if len(segment) >= min_length]
    if not usable:
        raise ValueError(f"No contiguous segment has at least {min_length} observations")
    dimensions = np.arange(1, args.max_dim + 1)
    segment_results = [run_fnn(segment, dimensions, args) for segment in usable]
    weights = np.asarray([max(1, len(segment) - args.max_dim * args.tau) for segment in usable], dtype=float)
    fractions = np.average(np.stack(segment_results), axis=0, weights=weights)

    rows = []
    for index, dim in enumerate(dimensions):
        rows.append(
            {
                "dimension": int(dim),
                "tau_hours": args.tau,
                "R_test_I": args.R,
                "A_test_II": args.A,
                "theiler_window": args.window,
                "maxnum": args.maxnum,
                "segments_used": len(usable),
                "fraction_test_I": f"{fractions[0, index]:.12g}",
                "fraction_test_II": f"{fractions[1, index]:.12g}",
                "fraction_either_test": f"{fractions[2, index]:.12g}",
                "threshold": args.threshold,
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "dataset": "berlin_temperature_2023_fnn",
        "source": {"path": str(source), "sha256": sha256(source), "column": args.column},
        "series": {
            "rows_in_source": len(series),
            "observations_used": sum(len(segment) for segment in usable),
            "missing_rows": missing,
            "all_contiguous_segment_lengths": [len(segment) for segment in segments],
            "usable_segment_lengths": [len(segment) for segment in usable],
        },
        "environment": {
            "python": platform.python_version(),
            "nolitsa": importlib.metadata.version("nolitsa"),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "numba": importlib.metadata.version("numba"),
        },
        "parameters": {
            "tau_hours": args.tau,
            "max_dimension": args.max_dim,
            "R_test_I": args.R,
            "A_test_II": args.A,
            "theiler_window": args.window,
            "maxnum": args.maxnum,
            "threshold": args.threshold,
            "library": "nolitsa.dimension.fnn",
        },
        "selection_diagnostics": {
            "first_dimension_test_I_below_threshold": first_below(fractions[0], args.threshold),
            "first_dimension_test_II_below_threshold": first_below(fractions[1], args.threshold),
            "first_dimension_either_test_below_threshold": first_below(fractions[2], args.threshold),
        },
        "interpretation": "Diagnostic only; final lag count requires temporal predictive ablation. Missing values split the series; no interpolation is used.",
        "output": {"path": str(output.relative_to(REPO)), "sha256": sha256(output)},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
