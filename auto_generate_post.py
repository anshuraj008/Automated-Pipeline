#!/usr/bin/env python3
"""Automatically create linkedin_post.json and image_prompt.txt from the latest fetched news."""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
NEWS_PATH = os.path.join(PROJECT_ROOT, "ai_news_data.json")
POST_PATH = os.path.join(PROJECT_ROOT, "linkedin_post.json")
PROMPT_PATH = os.path.join(PROJECT_ROOT, "image_prompt.txt")


def main():
    if not os.path.exists(NEWS_PATH):
        print(f"Error: {NEWS_PATH} not found. Run fetch_ai_news_rss.py first.")
        sys.exit(1)

    with open(NEWS_PATH, "r", encoding="utf-8") as f:
        news_items = json.load(f)

    if not news_items:
        print("Error: No news items found in ai_news_data.json.")
        sys.exit(1)

    top_story = news_items[0]
    title = top_story.get("title", "").strip()
    source_url = top_story.get("url", "").strip()
    source = top_story.get("source", "Tech Update").strip()
    category = top_story.get("category", "Technology").strip()
    description = top_story.get("description", "").strip()

    # Truncate caption to <= 280 chars
    max_len = 280
    caption_text = f"[{category}] {title}"
    if description and len(caption_text) + len(description) + 3 <= max_len:
        caption_text = f"{caption_text}: {description}"

    if len(caption_text) > max_len:
        caption_text = caption_text[: max_len - 3] + "..."

    post_data = {
        "caption": caption_text,
        "source_url": source_url,
        "headline": title,
    }

    with open(POST_PATH, "w", encoding="utf-8") as f:
        json.dump(post_data, f, indent=2)

    prompt_text = (
        f"A professional 1080x1080 social media graphic illustrating {title}. "
        f"Modern clean editorial layout, dark charcoal (#121212) background, "
        f"vibrant cyan accent lighting, high-contrast typography, minimal labels, "
        f"4k crisp render quality, verified source: {source}."
    )

    with open(PROMPT_PATH, "w", encoding="utf-8") as f:
        f.write(prompt_text)

    print(f"Auto-generated linkedin_post.json and image_prompt.txt for top story: {title[:50]}...")


if __name__ == "__main__":
    main()
