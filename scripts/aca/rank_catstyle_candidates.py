#!/usr/bin/env python3
"""CLI: rank Catstyle planet-pair aspect candidates (deterministic v0)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_candidate_ranker import rank_catstyle_candidates


def _load_candidates(args: argparse.Namespace) -> list:
    if args.candidates_json is not None:
        data = json.loads(args.candidates_json)
    elif args.input is not None:
        path = args.input.expanduser().resolve()
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        raise SystemExit("Provide --candidates-json or --input.")
    if not isinstance(data, list):
        raise SystemExit("Candidates JSON must be a list of objects.")
    return data


def _print_readable(result) -> None:
    print()
    print("Catstyle candidate ranking (v0, deterministic)")
    print(f"  Supported ranked: {len(result.ranked)}")
    print(f"  Unsupported:      {len(result.unsupported)}")
    print()
    for i, c in enumerate(result.ranked, start=1):
        print(f"{i}. {c.planet_a} + {c.planet_b} ({c.aspect_type})")
        orb_line = f"   orb={c.orb} deg  orb_bonus=+{c.orb_bonus}\n" if c.orb is not None else ""
        print(
            f"   total={c.total_score}  visual={c.visual_score} emotional={c.emotional_score} "
            f"comedy={c.comedy_score} clarity={c.clarity_score}  source={c.source}"
        )
        if orb_line:
            print(orb_line, end="")
        print(f"   mode: {c.mode_recommendation}")
        print(f"   angle: {c.recommended_scene_angle}")
        print(f"   reason: {c.reason}")
        print()
    if result.unsupported:
        print("Unsupported (not ranked as Catstyle v0 content candidates)")
        for u in result.unsupported:
            print(f"  - {u.planet_a} + {u.planet_b} ({u.aspect_type}): {u.reason}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank Catstyle aspect candidates for visual posting strength.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--candidates-json",
        dest="candidates_json",
        help='Inline JSON array, e.g. \'[{"planet_a":"Pluto","planet_b":"Venus","aspect_type":"conjunction"}]\'',
    )
    src.add_argument("--input", type=Path, help="Path to JSON file containing a candidate array")
    ap.add_argument("--output", type=Path, default=None, help="Write full JSON result to this path")
    args = ap.parse_args()

    try:
        candidates = _load_candidates(args)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(str(e), file=sys.stderr)
        return 1

    result = rank_catstyle_candidates(candidates)
    _print_readable(result)

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = result.model_dump(mode="json")
        out_path.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
