"""Exploratory plots and occupancy helpers for the datagen EDA notebook / CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from datagen.tables import DATASET_NAMES


@dataclass(frozen=True)
class EdaResult:
    figures_dir: Path
    figure_paths: dict[str, Path]
    occupancy_mean: float


def load_datasets(dataset_dir: Path) -> dict[str, pd.DataFrame]:
    datasets: dict[str, pd.DataFrame] = {}
    for name in DATASET_NAMES:
        path = dataset_dir / f"{name}.parquet"
        if not path.is_file():
            raise FileNotFoundError(path)
        datasets[name] = pd.read_parquet(path)
    return datasets


def nightly_occupancy(
    bookings: pd.DataFrame,
    nights: pd.DataFrame,
    rooms_by_type: dict[str, int],
) -> pd.DataFrame:
    """
    Realized occupancy per (date, room_type) from non-cancelled bookings.

    Returns columns: date, room_type, rooms_sold, capacity, occupancy.
    """
    capacity_rows = []
    for row in nights[["date", "room_type"]].itertuples(index=False):
        day = pd.Timestamp(row.date).date()
        code = str(row.room_type)
        capacity_rows.append(
            {
                "date": pd.Timestamp(day),
                "room_type": code,
                "capacity": rooms_by_type[code],
                "rooms_sold": 0,
            }
        )
    base = pd.DataFrame(capacity_rows)
    if base.empty:
        return base.assign(occupancy=pd.Series(dtype="float64"))

    if bookings.empty:
        base["occupancy"] = 0.0
        return base

    sold: dict[tuple[object, str], int] = {}
    active = bookings.loc[~bookings["cancelled"]]
    for row in active.itertuples(index=False):
        check_in = pd.Timestamp(row.check_in).date()
        room_type = str(row.room_type)
        for i in range(int(row.nights)):
            day = check_in + timedelta(days=i)
            key = (pd.Timestamp(day), room_type)
            sold[key] = sold.get(key, 0) + 1

    rooms_sold = []
    for row in base.itertuples(index=False):
        rooms_sold.append(sold.get((row.date, row.room_type), 0))
    base["rooms_sold"] = rooms_sold
    base["occupancy"] = base["rooms_sold"] / base["capacity"]
    return base


def _plotting():
    """Lazy import so `datagen run` works when matplotlib DLLs are blocked."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    from statsmodels.tsa.seasonal import seasonal_decompose

    return plt, sns, seasonal_decompose


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt = _plotting()[0]
    plt.close(fig)
    return path


def plot_seasonal_decomposition(calendar: pd.DataFrame, path: Path) -> Path:
    plt, _, seasonal_decompose = _plotting()
    series = (
        calendar.sort_values("date").set_index("date")["calendar_factor"].astype(float).asfreq("D")
    )
    series = series.interpolate(limit_direction="both")
    period = 7 if len(series) >= 14 else max(2, len(series) // 2)
    result = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="period")
    fig = result.plot()
    fig.set_size_inches(10, 8)
    fig.suptitle("Seasonal decomposition of calendar_factor", y=1.02)
    return _save(fig, path)


def plot_occupancy_histogram(occupancy: pd.DataFrame, path: Path) -> Path:
    plt, _, _ = _plotting()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(occupancy["occupancy"], bins=20, color="#2c6e49", edgecolor="white")
    ax.set_xlabel("Occupancy rate")
    ax.set_ylabel("Night-type count")
    ax.set_title("Occupancy histogram (non-cancelled bookings)")
    mean = float(occupancy["occupancy"].mean()) if len(occupancy) else 0.0
    ax.axvline(mean, color="#bc4749", linestyle="--", label=f"mean={mean:.2%}")
    ax.legend()
    return _save(fig, path)


def plot_price_demand_scatter(nights: pd.DataFrame, path: Path) -> Path:
    plt, sns, _ = _plotting()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=nights,
        x="demand_latent",
        y="optimal_price",
        hue="room_type",
        ax=ax,
        alpha=0.75,
    )
    ax.set_title("Price–demand scatter (optimal_price vs latent demand)")
    ax.set_xlabel("Latent demand D")
    ax.set_ylabel("Optimal price p* (PLN)")
    return _save(fig, path)


def plot_correlation_heatmap(snapshots: pd.DataFrame, path: Path) -> Path:
    plt, sns, _ = _plotting()
    numeric = snapshots.select_dtypes(include=[np.number])
    corr = numeric.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Snapshot feature correlation heatmap")
    return _save(fig, path)


def plot_event_uplift(nights: pd.DataFrame, occupancy: pd.DataFrame, path: Path) -> Path:
    plt, _, _ = _plotting()
    merged = nights.merge(
        occupancy[["date", "room_type", "occupancy"]],
        on=["date", "room_type"],
        how="left",
    )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    daily = (
        merged.groupby("date", as_index=False)
        .agg(event_uplift=("event_uplift", "mean"), occupancy=("occupancy", "mean"))
        .sort_values("date")
    )
    axes[0].plot(daily["date"], daily["event_uplift"], color="#1d3557", linewidth=1.2)
    axes[0].set_title("Mean event uplift over time")
    axes[0].set_ylabel("event_uplift")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].scatter(
        merged["event_uplift"],
        merged["occupancy"],
        alpha=0.5,
        c="#457b9d",
        edgecolors="none",
    )
    axes[1].set_xlabel("event_uplift")
    axes[1].set_ylabel("occupancy")
    axes[1].set_title("Event uplift vs realized occupancy")
    return _save(fig, path)


def run_eda(
    *,
    dataset_dir: Path,
    figures_dir: Path,
    rooms_by_type: dict[str, int],
) -> EdaResult:
    """Build the five Phase-4 EDA figures and return paths + mean occupancy."""
    datasets = load_datasets(dataset_dir)
    occupancy = nightly_occupancy(datasets["bookings"], datasets["nights"], rooms_by_type)
    mean_occ = float(occupancy["occupancy"].mean()) if len(occupancy) else 0.0

    paths = {
        "seasonal_decomposition": plot_seasonal_decomposition(
            datasets["calendar"], figures_dir / "seasonal_decomposition.png"
        ),
        "occupancy_histogram": plot_occupancy_histogram(
            occupancy, figures_dir / "occupancy_histogram.png"
        ),
        "price_demand_scatter": plot_price_demand_scatter(
            datasets["nights"], figures_dir / "price_demand_scatter.png"
        ),
        "correlation_heatmap": plot_correlation_heatmap(
            datasets["snapshots"], figures_dir / "correlation_heatmap.png"
        ),
        "event_uplift": plot_event_uplift(
            datasets["nights"], occupancy, figures_dir / "event_uplift.png"
        ),
    }
    return EdaResult(figures_dir=figures_dir, figure_paths=paths, occupancy_mean=mean_occ)
