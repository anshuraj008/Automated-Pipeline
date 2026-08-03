#!/usr/bin/env python3
"""Validate Antigravity output, build a schedule, and use Buffer."""

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode:
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Antigravity's one AI post and schedule it."
    )
    parser.add_argument(
        "--image-url",
        required=True,
        help="Public HTTPS URL of the Antigravity-generated image",
    )
    parser.add_argument(
        "--target",
        choices=["linkedin", "both"],
        default="both",
        help="Buffer target; both sends the same post to LinkedIn and X",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Schedule after the dry-run preview",
    )
    parser.add_argument(
        "--start-tomorrow",
        action="store_true",
        help="Schedule tomorrow instead of today",
    )
    args = parser.parse_args()
    py = sys.executable

    print("STEP 1/3 — Validating Antigravity output")
    run([py, "validate_antigravity_output.py"])

    print("STEP 2/3 — Building exactly one Buffer post")
    build_cmd = [py, "build_schedule.py", "--target", args.target, "--image-url", args.image_url]
    if args.start_tomorrow:
        build_cmd.append("--start-tomorrow")
    run(build_cmd)

    print("STEP 3/3 — Buffer dry run")
    run([py, "schedule_via_buffer.py", "--schedule-file", "schedule.json", "--dry-run"])

    if args.live:
        print("LIVE — Scheduling one post to Buffer")
        run([py, "schedule_via_buffer.py", "--schedule-file", "schedule.json"])
        print("Done. One Antigravity-generated AI update was scheduled.")
    else:
        print("Dry run complete. Add --live to schedule the post.")


if __name__ == "__main__":
    main()
