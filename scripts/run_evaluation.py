"""Separate real-telemetry preparation, costly model runs, and semantic review."""

import argparse
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.benchmark import evaluate, prepare
from evals.corpus import cleanup
from evals.scoring import report


def stop(signum, frame):
    raise KeyboardInterrupt()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--seconds", type=int, default=180, choices=range(120, 301))
    capture.add_argument("--scenario", action="append")
    model = sub.add_parser("evaluate")
    model.add_argument("--corpora", type=Path, required=True)
    model.add_argument("--model", default="gpt-5.6-luna")
    model.add_argument("--repeats", type=int, default=3)
    model.add_argument("--wait-for-capture", action="store_true")
    model.add_argument("--token-cap", type=int, default=4_000_000)
    reporting = sub.add_parser("report")
    reporting.add_argument("--corpora", type=Path, required=True)
    reporting.add_argument("--reviews", type=Path, required=True)
    reporting.add_argument("--output", type=Path, required=True)
    sub.add_parser("cleanup", help="Restore only the persisted local evaluation fault")
    args = parser.parse_args(argv)
    previous = signal.signal(signal.SIGTERM, stop)
    try:
        if args.command == "capture":
            prepare(args.output, seconds=args.seconds, selected=args.scenario)
        elif args.command == "evaluate":
            evaluate(args.corpora, model=args.model, repeats=args.repeats,
                     wait_for_capture=args.wait_for_capture, aggregate_token_cap=args.token_cap)
        elif args.command == "report":
            report(args.corpora, args.reviews, args.output)
        else:
            cleanup()
        return 0
    except KeyboardInterrupt:
        print("Evaluation interrupted; context-managed owned fault cleanup was attempted.", file=sys.stderr)
        return 130
    except (ValueError, OSError) as exc:
        print(f"Evaluation stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    sys.exit(main())
