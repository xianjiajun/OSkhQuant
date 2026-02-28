from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd


@dataclass(frozen=True)
class BacktestResult:
    output_dir: str
    trades: pd.DataFrame
    daily_stats: pd.DataFrame
    summary: pd.DataFrame
    benchmark: pd.DataFrame
    config: pd.DataFrame


def required_files() -> List[str]:
    return [
        "trades.csv",
        "daily_stats.csv",
        "summary.csv",
        "benchmark.csv",
        "config.csv",
    ]


def _require_file(dir_path: Path, name: str) -> Path:
    p = dir_path / name
    if not p.is_file():
        raise FileNotFoundError(f"Missing required artifact: {p}")
    return p


def parse_backtest_dir(output_dir: str) -> BacktestResult:
    dir_path = Path(output_dir)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Backtest output_dir not found: {dir_path}")

    trades_path = _require_file(dir_path, "trades.csv")
    daily_stats_path = _require_file(dir_path, "daily_stats.csv")
    summary_path = _require_file(dir_path, "summary.csv")
    benchmark_path = _require_file(dir_path, "benchmark.csv")
    config_path = _require_file(dir_path, "config.csv")

    trades = pd.read_csv(trades_path)
    daily_stats = pd.read_csv(daily_stats_path)
    summary = pd.read_csv(summary_path)
    benchmark = pd.read_csv(benchmark_path)
    config = pd.read_csv(config_path)

    return BacktestResult(
        output_dir=str(dir_path),
        trades=trades,
        daily_stats=daily_stats,
        summary=summary,
        benchmark=benchmark,
        config=config,
    )
