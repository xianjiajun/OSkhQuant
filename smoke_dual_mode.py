from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="KHQuant dual-mode smoke checks")
    parser.add_argument("--config", help="Path to .kh config file")
    parser.add_argument("--strategy", help="Path to strategy .py file")
    parser.add_argument("--allow-period-mismatch", action="store_true")
    parser.add_argument("--init-data-enabled", choices=["true", "false"], help="Override init-data behavior")
    args = parser.parse_args(argv)

    evidence_dir = Path(".sisyphus") / "evidence"
    ok_path = evidence_dir / "task-10-smoke-happy.txt"
    err_path = evidence_dir / "task-10-smoke-error.txt"

    try:
        # Reset both evidence files each run.
        _write(err_path, "")

        from api import run_backtest

        import khFrame  # noqa: F401

        lines = []
        lines.append("rc=0")
        lines.append("import: ok")
        lines.append(f"run_backtest callable: {callable(run_backtest)}")

        if args.config and args.strategy:
            init_data_enabled = None
            if args.init_data_enabled == "true":
                init_data_enabled = True
            elif args.init_data_enabled == "false":
                init_data_enabled = False

            result = run_backtest(
                args.config,
                args.strategy,
                allow_period_mismatch=args.allow_period_mismatch,
                init_data_enabled=init_data_enabled,
            )
            lines.append(f"output_dir: {result.output_dir}")
            out_dir = Path(result.output_dir)
            required = [
                "trades.csv",
                "daily_stats.csv",
                "summary.csv",
                "benchmark.csv",
                "config.csv",
            ]
            missing = [name for name in required if not (out_dir / name).is_file()]
            lines.append(f"missing_files: {missing}")
            if missing:
                raise FileNotFoundError(f"Missing artifacts: {missing}")
        else:
            lines.append("mode: import-only")
            lines.append("note: pass --config and --strategy to run a real backtest")

        _write(ok_path, "\n".join(lines) + "\n")
        return 0
    except Exception as e:
        import traceback

        _write(ok_path, "")
        _write(
            err_path,
            "\n".join(
                [
                    "rc=1",
                    f"smoke failed: {type(e).__name__}: {e}",
                    "traceback:",
                    traceback.format_exc().rstrip(),
                    "",
                ]
            ),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
