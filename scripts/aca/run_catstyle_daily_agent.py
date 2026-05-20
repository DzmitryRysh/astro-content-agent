#!/usr/bin/env python3
"""CLI: orchestrate full Catstyle daily pipeline (jobs → images → package → review → handoff → optional publish)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import REPO_ROOT, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_daily_agent import run_catstyle_daily_agent


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Catstyle daily agent: build image jobs, execute with provider, post package, manual review, "
            "optional approval + publish handoff, optional Instagram publish (same stack as publish_catstyle_real.py). "
            "Planet glyphs use the canonical Catstyle registry in prompts; flags carry integrated symbols by default "
            "(no separate overlay step)."
        ),
    )
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--work-root",
        type=Path,
        default=None,
        help="Working directory for catstyle_image_jobs/, catstyle_post_packages/, catstyle_publish_handoffs/ (default: cwd)",
    )
    ap.add_argument("--provider", choices=("stub", "openai_image"), default="stub", help="Image executor provider")
    ap.add_argument("--scan-mode", choices=("noon", "day-window"), default="day-window")
    ap.add_argument("--step-hours", type=int, default=2)
    ap.add_argument("--editorial-profile", choices=("charged", "balanced", "supportive"), default="charged")
    ap.add_argument("--world-template", default="cosmic_zodiac_arena")
    ap.add_argument("--scene-template", default=None)
    ap.add_argument("--render-style-profile", default="premium_comic_poster_v2")
    ap.add_argument("--shot-mode", choices=("hero_pair", "epic_arena_showdown", "standard"), default="epic_arena_showdown")
    ap.add_argument("--jobs-count", type=int, choices=(1, 2), default=1)
    ap.add_argument("--planet-a", default=None, dest="planet_a")
    ap.add_argument("--planet-b", default=None, dest="planet_b")
    ap.add_argument("--aspect-type", default=None, dest="aspect_type")
    ap.add_argument("--mode", default=None, dest="mode")
    ap.add_argument(
        "--style-reference-image",
        default=None,
        dest="style_reference_image",
        help="Optional explicit style reference image path.",
    )
    ap.add_argument(
        "--disable-approved-reference-auto",
        action="store_true",
        dest="disable_approved_reference_auto",
        help="Disable approved-registry auto style reference.",
    )
    ap.add_argument(
        "--approve",
        action="store_true",
        help="Approve manual review when QC is ready (writes publish handoff). "
        "Also implied when --validate-only or --publish is set.",
    )
    ap.add_argument("--approval-notes", default="", help="Reviewer notes when approving")
    ap.add_argument(
        "--validate-only",
        action="store_true",
        help="After handoff, run publish prerequisites + validate-only (no Instagram publish). "
        "If both --publish and --validate-only are set, validate-only wins.",
    )
    ap.add_argument("--publish", action="store_true", help="After handoff, run real Instagram publish (requires env + DB)")
    ap.add_argument(
        "--force-publish-unstable",
        action="store_true",
        dest="force_publish_unstable",
        help=(
            "Override creative publish safety gate: allow real --publish even when this pair has no approved "
            "reference or stable visual canon (logged prominently)."
        ),
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing package/review/handoff/executor outputs")
    ap.add_argument("--brand-profile-id", default=None)
    ap.add_argument("--instagram-account-id", default=None)
    ap.add_argument("--json", action="store_true", help="Print CatstyleDailyAgentResult fields as JSON")

    args = ap.parse_args()
    work = Path(args.work_root).expanduser().resolve() if args.work_root else Path.cwd().resolve()

    try:
        r = run_catstyle_daily_agent(
            args.date,
            work_root=work,
            provider=args.provider,
            scan_mode=args.scan_mode,
            step_hours=args.step_hours,
            editorial_profile=args.editorial_profile,
            world_template=args.world_template,
            scene_template=args.scene_template,
            render_style_profile=args.render_style_profile,
            shot_mode=args.shot_mode,
            jobs_count=args.jobs_count,
            planet_a_override=args.planet_a,
            planet_b_override=args.planet_b,
            aspect_type_override=args.aspect_type,
            mode_override=args.mode,
            approve=args.approve,
            validate_only=args.validate_only,
            publish=args.publish,
            overwrite=args.overwrite,
            approval_notes=args.approval_notes,
            brand_profile_id=args.brand_profile_id,
            instagram_account_id=args.instagram_account_id,
            style_reference_image_path=args.style_reference_image,
            disable_approved_reference_auto=args.disable_approved_reference_auto,
            force_publish_unstable=args.force_publish_unstable,
            repo_root_for_dotenv=REPO_ROOT,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    if args.json:
        import json

        from dataclasses import asdict

        print(json.dumps(asdict(r), indent=2, ensure_ascii=False))
        return r.exit_code

    print()
    print("Catstyle daily agent")
    print(f"  date:              {r.date}")
    print(f"  exit_code:         {r.exit_code}")
    print(f"  status:            {r.status}")
    print(f"  selected_aspect:   {r.selected_aspect}")
    print(f"  manifest:          {r.manifest_path or '(n/a)'}")
    print(f"  image_jobs_dir:    {r.image_jobs_dir or '(n/a)'}")
    print(f"  generated_images:  {r.generated_images_dir or '(n/a)'}")
    print(f"  primary_image:     {r.primary_image_path or '(n/a)'}")
    print(f"  package_dir:       {r.package_dir or '(n/a)'}")
    print(f"  publish_handoff:   {r.publish_handoff_dir or '(n/a)'}")
    if r.publish_exit_code is not None:
        print(f"  publish_exit:      {r.publish_exit_code}")
    if r.publish_status:
        print(f"  publish_status:    {r.publish_status}")
    if r.publish_result_paths:
        print("  publish_artifacts:")
        for p in r.publish_result_paths:
            print(f"    - {p}")
    if r.errors:
        print("  errors:")
        for e in r.errors:
            print(f"    - {e}")
    for line in r.log_lines:
        print(f"  {line}")
    print()

    return r.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
