from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from backtest_result import BacktestResult, parse_backtest_dir
from khConfig import KhConfig
from khFrame import KhQuantFramework, PeriodMismatchError


def _check_period_mismatch_policy(config: KhConfig, *, allow_period_mismatch: bool) -> None:
    """Fast, deterministic period mismatch enforcement.

    This runs before framework.run() so headless callers get policy errors without
    requiring any trading/data initialization.
    """

    data_period = getattr(config, "kline_period", None) or config.config_dict.get("data", {}).get("kline_period", "tick")
    trigger_type = config.config_dict.get("backtest", {}).get("trigger", {}).get("type", "tick")

    if trigger_type == "custom":
        return

    period_consistency_map = {
        "tick": "tick",
        "1m": "1m",
        "5m": "5m",
        "1d": "1d",
    }
    expected = period_consistency_map.get(trigger_type, "tick")

    if data_period == expected:
        return

    if allow_period_mismatch:
        print(
            f"[WARNING] Period mismatch allowed: data_period={data_period} trigger_type={trigger_type} expected={expected}"
        )
        return

    raise PeriodMismatchError(
        "Period mismatch: data period does not match trigger type. Set allow_period_mismatch=True to continue."
    )


def run_backtest(
    config: Union[str, Path, KhConfig],
    strategy_file: Union[str, Path],
    *,
    allow_period_mismatch: bool = False,
    init_data_enabled: Optional[bool] = None,
) -> BacktestResult:
    if isinstance(config, KhConfig):
        config_path = Path(config.config_path)
    else:
        config_path = Path(config)

    strategy_path = Path(strategy_file)

    if not config_path.is_file():
        raise FileNotFoundError(f"Config path not found: {config_path}")
    if not strategy_path.is_file():
        raise FileNotFoundError(f"Strategy file not found: {strategy_path}")

    cfg = config if isinstance(config, KhConfig) else KhConfig(str(config_path))
    _check_period_mismatch_policy(cfg, allow_period_mismatch=allow_period_mismatch)

    framework = KhQuantFramework(
        str(config_path),
        str(strategy_path),
        trader_callback=None,
        init_data_enabled=init_data_enabled,
        allow_period_mismatch=allow_period_mismatch,
    )
    framework.run()

    output_dir = getattr(framework, "last_backtest_dir", None)
    if not output_dir:
        raise RuntimeError("Backtest finished but output_dir is unavailable")

    return parse_backtest_dir(output_dir)
