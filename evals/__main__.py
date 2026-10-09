"""Eval runner. Usage:

    python -m evals replay <agent>
    python -m evals live <agent> [--case ID] [--repeat K] [--judge] [--keep]
    python -m evals freeze <agent>
    python -m evals outcome fixture-analyst

Agents: data-collector, plan-builder, usage-collector, fixture-analyst.
"""

from __future__ import annotations

import argparse
import sys

AGENTS = ("data-collector", "plan-builder", "usage-collector", "fixture-analyst")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evals")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="grade the recorded runs (free)")
    replay.add_argument("agent", choices=AGENTS)
    live = sub.add_parser("live", help="run the agent headless and grade it (costs money)")
    live.add_argument("agent", choices=AGENTS)
    live.add_argument("--case", action="append", help="case id; repeatable (default: all)")
    live.add_argument("--repeat", type=int, default=1)
    live.add_argument("--judge", action="store_true", help="also run the model judge")
    live.add_argument("--keep", action="store_true", help="keep the temp workspace")
    freeze = sub.add_parser("freeze", help="re-freeze the replay fixtures from the archive")
    freeze.add_argument("agent", choices=AGENTS)
    outcome = sub.add_parser("outcome", help="season-level forecast quality (prints only)")
    outcome.add_argument("agent", choices=("fixture-analyst",))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.agent == "plan-builder":
        from evals.plan_builder import runner
    elif args.agent == "usage-collector":
        from evals.usage_collector import runner
    elif args.agent == "fixture-analyst":
        from evals.fixture_analyst import runner
    else:
        from evals.data_collector import runner

    if args.command == "replay":
        return runner.replay()
    if args.command == "freeze":
        return runner.freeze_fixtures()
    if args.command == "outcome":
        return runner.outcome()
    return runner.live(case_ids=args.case, repeat=args.repeat, judge=args.judge,
                       keep=args.keep)


if __name__ == "__main__":
    sys.exit(main())
