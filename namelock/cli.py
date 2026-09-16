"""namelock — fail a voice-agent call if the agent addresses the wrong person."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .check import check_text, load_transcript

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="namelock",
        description=(
            "Fail with exit 1 if the agent addresses a person other than the "
            "expected caller. Catches 'You're all set, Jordan' when the session "
            "is Alex."
        ),
    )
    parser.add_argument("file", help="transcript .txt or JSON with turns[]")
    parser.add_argument(
        "--expect-name",
        required=True,
        metavar="NAME",
        help="the caller this session is supposed to be talking to",
    )
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        metavar="NAME",
        help="also-allowed form of the expected name (repeatable)",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--version", action="version", version=f"namelock {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.file)
    if not path.is_file():
        print(f"namelock: no such file: {path}", file=sys.stderr)
        return EXIT_USAGE
    try:
        text = load_transcript(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"namelock: {exc}", file=sys.stderr)
        return EXIT_USAGE
    findings = check_text(text, args.expect_name, args.alias)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": not findings,
                    "expected": args.expect_name,
                    "findings": [
                        {"name": f.name, "line": f.line, "snippet": f.snippet}
                        for f in findings
                    ],
                },
                indent=2,
            )
        )
    else:
        if findings:
            print(f"namelock: expected {args.expect_name!r}, agent addressed someone else")
            for f in findings:
                print(f"  L{f.line}: {f.name}  ({f.snippet})")
        else:
            print(f"namelock: ok ({args.expect_name})")
    return EXIT_MISMATCH if findings else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
