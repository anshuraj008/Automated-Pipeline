#!/usr/bin/env python3
"""
Schedule posts through Buffer API for LinkedIn and X channels.

Usage:
  python3 schedule_via_buffer.py [--schedule-file schedule.json] [--dry-run]
  python3 schedule_via_buffer.py --single --linkedin "post text" --date 2026-06-13 --time "9:00 AM"

The schedule file JSON format:
{
  "channels": {
    "linkedin": "optional_override_channel_id",
    "x": "optional_override_channel_id"
  },
  "posts": [
    {
      "caption": "Post body text...",
      "type": "text",
      "date": "2026-06-13",
      "time_ist": "9:00 AM",
      "target": "both",
      "media_urls": [],
      "linkedin_first_comment": ""
    }
  ]
}

- type: "text", "image", or "carousel" (carousel treated as single image)
- target: "both" (default), "linkedin", or "x"
- media_urls: publicly hosted image URLs (Buffer fetches these at publish time)
- linkedin_first_comment: optional first comment on LinkedIn post
- time_ist: time in 12-hour IST format like "9:00 AM" or "6:00 PM"

Times are converted from IST (UTC+5:30) to UTC for the Buffer API.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from buffer_client import create_post, get_channels, get_organizations
from env_utils import get_env

IST_OFFSET = timedelta(hours=5, minutes=30)
UTC = timezone.utc

# LinkedIn hard-truncates/rejects posts beyond this length.
LINKEDIN_MAX_CHARS = 3000
# Buffer/X reject plain (non-thread) posts beyond this length.
X_MAX_CHARS = 280


def parse_time_ist_to_utc(date_str, time_ist):
    """Convert IST date + time to ISO 8601 UTC string."""
    clean_time = time_ist.strip().upper().replace("\u202f", " ").replace("\u00a0", " ")
    dt_ist = datetime.strptime(f"{date_str} {clean_time}", "%Y-%m-%d %I:%M %p")
    dt_ist = dt_ist.replace(tzinfo=timezone(IST_OFFSET))
    dt_utc = dt_ist.astimezone(UTC)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def fetch_channel_ids():
    """Fetch channel IDs from Buffer API and detect LinkedIn + X channels.

    `BUFFER_LINKEDIN_CHANNEL_ID` / `BUFFER_X_CHANNEL_ID` (from `.env` or the
    real environment) always win over auto-detection, as documented in
    README.md.
    """
    env_linkedin_id = get_env("BUFFER_LINKEDIN_CHANNEL_ID")
    env_x_id = get_env("BUFFER_X_CHANNEL_ID")

    print("Fetching organizations and channels from Buffer...")
    try:
        orgs = get_organizations()
    except Exception as e:
        print(f"Error fetching organizations: {e}")
        return None, env_linkedin_id, env_x_id

    if not orgs:
        print("No organizations found.")
        return None, env_linkedin_id, env_x_id

    org = orgs[0]
    org_id = org["id"]
    org_name = org["name"]
    print(f"Organization: {org_name} ({org_id})")

    channels = get_channels(org_id)
    linkedin_id = env_linkedin_id
    x_id = env_x_id

    for ch in channels:
        service = ch["service"]
        print(f"  Channel: {ch['name']} | {service} | {ch['id']}")
        if service == "linkedin" and not linkedin_id:
            linkedin_id = ch["id"]
        elif service == "twitter" and not x_id:
            x_id = ch["id"]

    if env_linkedin_id:
        print(f"Using BUFFER_LINKEDIN_CHANNEL_ID override: {env_linkedin_id}")
    if env_x_id:
        print(f"Using BUFFER_X_CHANNEL_ID override: {env_x_id}")
    if not linkedin_id:
        print("WARNING: No LinkedIn channel found in Buffer account.")
    if not x_id:
        print("WARNING: No X/Twitter channel found in Buffer account.")

    return org_id, linkedin_id, x_id


def build_assets(media_urls):
    """Convert media URLs list to Buffer assets array."""
    if not media_urls:
        return None
    assets = []
    for url in media_urls:
        assets.append({"image": {"url": url}})
    return assets


def schedule_posts(schedule, linkedin_id, x_id, dry_run=False):
    results = {"scheduled": [], "errors": []}

    posts = schedule.get("posts", [])
    if not posts:
        print("No posts found in schedule.")
        return results

    override_linkedin = schedule.get("channels", {}).get("linkedin")
    override_x = schedule.get("channels", {}).get("x")

    li_id = override_linkedin or linkedin_id
    x_ch_id = override_x or x_id

    for i, post in enumerate(posts):
        caption = post.get("caption", "").strip()
        post_type = post.get("type", "text")
        date_str = post.get("date")
        time_ist = post.get("time_ist")
        target = post.get("target", "both")
        media_urls = post.get("media_urls", [])
        first_comment = post.get("linkedin_first_comment", "")

        if not caption:
            print(f"Post {i + 1}: SKIP (empty caption)")
            continue

        due_at = None
        if date_str and time_ist:
            due_at = parse_time_ist_to_utc(date_str, time_ist)
        else:
            print(f"Post {i + 1}: SKIP (missing date or time)")
            continue

        assets = build_assets(media_urls)
        channels_to_post = []
        if target == "both":
            channels_to_post = [
                ("LinkedIn", li_id, first_comment if first_comment else None),
                ("X", x_ch_id, None),
            ]
        elif target == "linkedin":
            channels_to_post = [
                ("LinkedIn", li_id, first_comment if first_comment else None)
            ]
        elif target == "x":
            channels_to_post = [("X", x_ch_id, None)]

        for platform, channel_id, comment in channels_to_post:
            if not channel_id:
                print(f"Post {i + 1}: SKIP {platform} (no channel ID)")
                continue

            label = (
                f"Post {i + 1}/{len(posts)} | {platform} | {date_str} {time_ist} IST"
            )

            limit = LINKEDIN_MAX_CHARS if platform == "LinkedIn" else X_MAX_CHARS
            if len(caption) > limit and not assets:
                print(
                    f"  WARNING: {label} caption is {len(caption)} chars, "
                    f"over the {platform} limit of {limit}. Buffer may reject or truncate this post."
                )

            metadata = None
            if platform == "LinkedIn" and comment:
                metadata = {"linkedin": {"comment": comment}}

            if dry_run:
                print(f"[DRY RUN] {label}")
                print(f"  Caption ({len(caption)} chars): {caption[:120]}...")
                if assets:
                    print(f"  Media: {len(assets)} image(s)")
                if metadata:
                    print(f"  First comment: {comment[:80]}...")
                results["scheduled"].append({"platform": platform, "dry_run": True})
                continue

            try:
                post_result = create_post(
                    channel_id=channel_id,
                    text=caption,
                    due_at=due_at,
                    mode="customScheduled",
                    assets=assets,
                    metadata=metadata,
                )
                print(f"  {label} -> {post_result['id']}")
                results["scheduled"].append(post_result)
            except Exception as e:
                err_msg = f"{label}: {e}"
                print(f"  ERROR: {err_msg}")
                results["errors"].append({"platform": platform, "error": str(e)})

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Schedule LinkedIn/X posts via Buffer API"
    )
    parser.add_argument(
        "--schedule-file",
        default="./schedule.json",
        help="Path to JSON schedule file (default: ./schedule.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview posts without actually scheduling",
    )
    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="List available channels from Buffer and exit",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Schedule a single post via CLI args (use with --linkedin/--x)",
    )
    parser.add_argument("--linkedin", help="Post text for LinkedIn")
    parser.add_argument("--x", help="Post text for X")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format")
    parser.add_argument("--time", dest="time_ist", help="Time in IST (e.g. '9:00 AM')")
    parser.add_argument("--media", nargs="*", default=[], help="Public image URL(s)")
    parser.add_argument("--comment", help="LinkedIn first comment")

    args = parser.parse_args()

    if args.list_channels:
        fetch_channel_ids()
        return

    org_id, linkedin_id, x_id = fetch_channel_ids()

    if args.single:
        if not args.linkedin and not args.x:
            print("Error: --single requires --linkedin and/or --x text")
            sys.exit(1)
        schedule = {"posts": []}
        post = {
            "caption": args.linkedin or args.x,
            "type": "image" if args.media else "text",
            "date": args.date or datetime.now().strftime("%Y-%m-%d"),
            "time_ist": args.time_ist or "9:00 AM",
            "target": "both"
            if (args.linkedin and args.x)
            else ("linkedin" if args.linkedin else "x"),
            "media_urls": args.media,
        }
        if args.comment:
            post["linkedin_first_comment"] = args.comment
        schedule["posts"].append(post)
    else:
        try:
            with open(args.schedule_file) as f:
                schedule = json.load(f)
        except FileNotFoundError:
            print(f"Schedule file not found: {args.schedule_file}")
            print("Create a schedule.json file or use --single to post directly.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in schedule file: {e}")
            sys.exit(1)

    if args.dry_run:
        print("\n=== DRY RUN MODE - No posts will be scheduled ===\n")

    result = schedule_posts(schedule, linkedin_id, x_id, dry_run=args.dry_run)

    print(
        f"\nDone. Scheduled: {len(result['scheduled'])}, Errors: {len(result['errors'])}"
    )
    if result["errors"]:
        print("Errors:")
        for e in result["errors"]:
            print(f"  - {e['platform']}: {e['error']}")


if __name__ == "__main__":
    main()
