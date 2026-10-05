"""Export an acknowledged, reviewed run or verify the checked-in public bundle."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sentinel.replay import Replay, build_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="Validate an existing public bundle without private artifacts")
    parser.add_argument("--run", type=Path)
    parser.add_argument("--exercise", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.check:
            replay = Replay.model_validate_json(args.check.read_bytes())
            print(f"Public replay verified: {replay.run_id}; {len(replay.evidence)} evidence records.")
            return 0
        if not all((args.run, args.exercise, args.review, args.output)):
            parser.error("Export requires --run, --exercise, --review, and --output")
        review = json.loads(args.review.read_bytes())
        result = build_replay(args.run, args.exercise, review)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(f"Exported reviewed replay: {result['run_id']}; {len(result['evidence'])} evidence records.")
        return 0
    except (OSError, ValueError, KeyError, IndexError) as exc:
        # Validation exceptions can echo credential-like values; print only type.
        print(f"Replay export failed: {type(exc).__name__}; inspect inputs privately.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
