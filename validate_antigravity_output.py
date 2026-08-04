#!/usr/bin/env python3
"""Validate the post and image prompt written by Antigravity."""

import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
POST_PATH = os.path.join(PROJECT_ROOT, "linkedin_post.json")
PROMPT_PATH = os.path.join(PROJECT_ROOT, "image_prompt.txt")


def main():
    if not os.path.exists(POST_PATH):
        raise SystemExit("Antigravity must create linkedin_post.json first.")
    if not os.path.exists(PROMPT_PATH):
        raise SystemExit("Antigravity must create image_prompt.txt first.")

    with open(POST_PATH) as f:
        post = json.load(f)
    caption = str(post.get("caption", "")).strip()
    if not caption:
        raise SystemExit("linkedin_post.json has an empty caption.")
    if len(caption) > 3000:
        raise SystemExit(f"Caption is {len(caption)} characters; maximum is 3000.")

    if not post.get("source_url"):
        raise SystemExit("linkedin_post.json must include source_url.")

    with open(PROMPT_PATH) as f:
        prompt = f.read().strip()
    if len(prompt) < 120:
        raise SystemExit("image_prompt.txt is too short for a quality image brief.")

    print("Antigravity output validated.")
    print(f"Caption: {len(caption)} characters")
    print("Image prompt: present")


if __name__ == "__main__":
    main()
