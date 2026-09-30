"""Utilities for the hybrid Berlin district/sector allocation.

The functions in this module deliberately separate three quantities:

* ``district_share`` allocates the Berlin hourly aggregate to districts;
* ``share_<sector>`` allocates a district total to sectors; and
* ``rake_proportional`` reconciles proxy matrices with trusted row/column
  totals without changing their relative pattern more than necessary.

No German source is loaded here.  Source paths, mappings and imputation flags
belong to the calling pipeline and must be recorded in its manifest.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


MODEL_SECTORS: tuple[str, ...] = ("I", "R", "C", "P", "T")


def calculate_monthly_shares(
    observations: pd.DataFrame,
    *,
    district_col: str = "district",
    year_col: str = "year",
    month_col: str = "month",
    sector_energy_cols: Mapping[str, str] | None = None,
    city_totals: pd.DataFrame | None = None,
    city_total_col: str = "city_total_MWh",
) -> pd.DataFrame:
    """Calculate district/sector shares from monthly energy observations.

    ``observations`` must contain one or more rows identified by
    ``district_col``, ``year_col`` and ``month_col`` and non-negative MWh
    columns.  Repeated keys are summed before the shares are calculated.
    ``city_totals`` may provide an externally reconciled Berlin total with the
    same year/month keys.  Without it, the city denominator is the sum of the
    districts present in ``observations`` and is therefore a *coverage* total.

    Rows with zero total receive zero sector shares and are flagged.  The
    function never silently converts missing data into zero.
    """
    if sector_energy_cols is None:
        sector_energy_cols = {
            sector: f"consumo_{sector}_MWh" for sector in MODEL_SECTORS
        }
    sectors = tuple(sector_energy_cols)
    if not sectors:
        raise ValueError("At least one sector energy column is required")

    keys = [district_col, year_col, month_col]
    required = keys + list(sector_energy_cols.values())
    missing = [column for column in required if column not in observations.columns]
    if missing:
        raise KeyError(f"Missing monthly energy columns: {missing}")

    data = observations[required].copy()
    for column in sector_energy_cols.values():
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if data[column].isna().any():
            raise ValueError(f"Non-numeric or missing values in {column}")
        if (data[column] < 0).any():
            raise ValueError(f"Negative energy values in {column}")

    data = data.groupby(keys, as_index=False, dropna=False)[
        list(sector_energy_cols.values())
    ].sum()
    energy_columns = list(sector_energy_cols.values())
    data["district_total_MWh"] = data[energy_columns].sum(axis=1)
    positive = data["district_total_MWh"] > 0
    data["zero_total_flag"] = ~positive

    for sector, energy_column in sector_energy_cols.items():
        share_column = f"share_{sector}"
        data[share_column] = 0.0
        data.loc[positive, share_column] = (
            data.loc[positive, energy_column]
            / data.loc[positive, "district_total_MWh"]
        )

    period_keys = [year_col, month_col]
    if city_totals is None:
        totals = (
            data.groupby(period_keys, as_index=False)["district_total_MWh"]
            .sum()
            .rename(columns={"district_total_MWh": city_total_col})
        )
    else:
        required_totals = period_keys + [city_total_col]
        missing_totals = [c for c in required_totals if c not in city_totals.columns]
        if missing_totals:
            raise KeyError(f"Missing city-total columns: {missing_totals}")
        totals = city_totals[required_totals].copy()
        totals[city_total_col] = pd.to_numeric(
            totals[city_total_col], errors="coerce"
        )
        if totals[city_total_col].isna().any() or (totals[city_total_col] < 0).any():
            raise ValueError("City totals must be finite and non-negative")

    data = data.merge(totals, on=period_keys, how="left", validate="many_to_one")
    if data[city_total_col].isna().any():
        raise ValueError("A district month has no matching city total")
    data["district_share"] = 0.0
    has_city_total = data[city_total_col] > 0
    data.loc[has_city_total, "district_share"] = (
        data.loc[has_city_total, "district_total_MWh"]
        / data.loc[has_city_total, city_total_col]
    )
    return data


def rake_proportional(
    seed: pd.DataFrame,
    *,
    row_col: str,
    column_totals: Mapping[str, float],
    row_totals: Mapping[object, float],
    columns: Sequence[str],
    max_iter: int = 10_000,
    tolerance: float = 1e-9,
) -> pd.DataFrame:
    """Reconcile a non-negative proxy matrix to trusted row/column totals.

    This is iterative proportional fitting.  Zero cells remain zero, so the
    caller must provide a positive seed wherever a district-sector cell is
    physically possible.  The returned long-form table contains ``row_col``
    and one column per sector in ``columns``.
    """
    if not columns:
        raise ValueError("No matrix columns were provided")
    if set(columns) != set(column_totals):
        raise ValueError("Column totals and matrix columns differ")
    rows = list(row_totals)
    if set(seed[row_col]) != set(rows):
        raise ValueError("Seed rows and row totals differ")
    matrix = seed.set_index(row_col)[list(columns)].astype(float).reindex(rows)
    if matrix.isna().any().any() or (matrix < 0).any().any():
        raise ValueError("Seed matrix must be finite and non-negative")

    target_rows = pd.Series(row_totals, dtype=float).reindex(rows)
    target_cols = pd.Series(column_totals, dtype=float).reindex(columns)
    if (target_rows < 0).any() or (target_cols < 0).any():
        raise ValueError("Target totals must be non-negative")
    if not np.isclose(target_rows.sum(), target_cols.sum(), rtol=0, atol=tolerance):
        raise ValueError("Row and column totals do not have the same grand total")

    values = matrix.to_numpy(dtype=float)
    for _ in range(max_iter):
        row_sums = values.sum(axis=1)
        if np.any((row_sums == 0) & (target_rows.to_numpy() > tolerance)):
            raise ValueError("A positive row target has an all-zero seed row")
        row_factors = np.divide(
            target_rows.to_numpy(),
            row_sums,
            out=np.ones_like(row_sums),
            where=row_sums > 0,
        )
        values *= row_factors[:, None]

        col_sums = values.sum(axis=0)
        if np.any((col_sums == 0) & (target_cols.to_numpy() > tolerance)):
            raise ValueError("A positive column target has an all-zero seed column")
        col_factors = np.divide(
            target_cols.to_numpy(),
            col_sums,
            out=np.ones_like(col_sums),
            where=col_sums > 0,
        )
        values *= col_factors[None, :]
        if max(
            np.max(np.abs(values.sum(axis=1) - target_rows.to_numpy())),
            np.max(np.abs(values.sum(axis=0) - target_cols.to_numpy())),
        ) <= tolerance:
            break
    else:
        raise RuntimeError("Raking did not converge within max_iter")

    result = pd.DataFrame(values, index=rows, columns=columns).reset_index()
    result = result.rename(columns={"index": row_col})
    return result


def allocate_hourly_city_load(
    hourly_city: pd.DataFrame,
    monthly_shares: pd.DataFrame,
    *,
    timestamp_col: str = "timestamp",
    load_col: str = "city_predicted_MW",
    year_col: str = "year",
    month_col: str = "month",
    district_col: str = "district",
    sector_share_columns: Iterable[str] = (),
) -> pd.DataFrame:
    """Expand an hourly Berlin aggregate into district-sector rows.

    ``monthly_shares`` must contain ``district_col``, year/month, a
    ``district_share`` and the requested sector share columns.  The city load
    is conserved at each timestamp up to floating-point precision.
    """
    shares = list(sector_share_columns)
    required = [district_col, year_col, month_col, "district_share"] + shares
    missing = [column for column in required if column not in monthly_shares.columns]
    if missing:
        raise KeyError(f"Missing allocation columns: {missing}")
    data = hourly_city.copy()
    if timestamp_col in data.columns:
        stamp = pd.to_datetime(data[timestamp_col])
        data[year_col] = stamp.dt.year
        data[month_col] = stamp.dt.month
    elif not {year_col, month_col}.issubset(data.columns):
        raise KeyError("Hourly data needs a timestamp or year/month columns")

    data = data.merge(
        monthly_shares[required],
        on=[year_col, month_col],
        how="left",
        validate="many_to_many",
    )
    if data["district_share"].isna().any():
        raise ValueError("Some hourly rows have no monthly district weights")
    data["district_predicted_MW"] = data[load_col] * data["district_share"]
    for share_column in shares:
        sector = share_column.removeprefix("share_")
        data[f"sector_{sector}_predicted_MW"] = (
            data["district_predicted_MW"] * data[share_column]
        )
    return data
