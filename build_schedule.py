#!/usr/bin/env python3
"""Build a schedule containing exactly one current AI-news post."""

import argparse
import json
import os
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-file", default="linkedin_post.json")
    parser.add_argument("--image-url", help="Public Antigravity-generated image URL")
    parser.add_argument("--output", default="schedule.json")
    parser.add_argument("--target", choices=["linkedin", "both"], default="both")
    parser.add_argument("--start-tomorrow", action="store_true")
    parser.add_argument("--time", default="9:00 AM", help="IST publish time")
    args = parser.parse_args()

    with open(os.path.join(PROJECT_ROOT, args.post_file)) as f:
        post = json.load(f)

    caption = str(post.get("caption", "")).strip()
    if not caption:
        raise SystemExit("Generated post has no caption.")
    if len(caption) > 280 and args.target == "both":
        raise SystemExit(
            f"Post is {len(caption)} characters; a shared LinkedIn/X post must be <=280 characters."
        )

    publish_date = datetime.now().date()
    if args.start_tomorrow:
        publish_date += timedelta(days=1)

    schedule = {
        "channels": {"linkedin": "", "x": ""},
        "posts": [
            {
                "caption": caption,
                "type": "image" if args.image_url else "text",
                "date": publish_date.isoformat(),
                "time_ist": args.time,
                "target": args.target,
                "media_urls": [args.image_url] if args.image_url else [],
                "linkedin_first_comment": "",
                "source_url": post.get("source_url", ""),
            }
        ],
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    with open(output_path, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"Built {args.output} with exactly 1 post")
    print(f"  {publish_date} {args.time} IST | {args.target}")


if __name__ == "__main__":
    main()
