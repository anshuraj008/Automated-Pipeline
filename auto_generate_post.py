#!/usr/bin/env python3
"""Automatically create rich human-formatted linkedin_post.json and image_prompt.txt."""

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
    category = top_story.get("category", "Full Stack & Web Dev").strip()
    description = top_story.get("description", "").strip()

    clean_desc = description.replace("\n", " ").strip()
    if len(clean_desc) > 350:
        clean_desc = clean_desc[:350] + "..."

    # Determine CS Engineering Category Tag & Hashtags
    cat_lower = category.lower()
    if "full stack" in cat_lower or "react" in cat_lower or "node" in cat_lower:
        cat_badge = "[Full Stack Development]"
        hashtags = [
            "#FullStackDevelopment",
            "#WebDevelopment",
            "#Frontend",
            "#Backend",
            "#SystemDesign",
            "#SoftwareEngineering",
            "#SelfGrowth",
            "#TechCommunity",
        ]
    elif "dsa" in cat_lower or "algorithm" in cat_lower or "python" in cat_lower:
        cat_badge = "[DSA & Algorithms]"
        hashtags = [
            "#DataStructures",
            "#Algorithms",
            "#DSA",
            "#ProblemSolving",
            "#ComputerScience",
            "#SoftwareEngineering",
            "#SelfGrowth",
            "#TechCommunity",
        ]
    elif "system design" in cat_lower or "architecture" in cat_lower or "devops" in cat_lower:
        cat_badge = "[System Design & Architecture]"
        hashtags = [
            "#SystemDesign",
            "#SoftwareArchitecture",
            "#DistributedSystems",
            "#Backend",
            "#SoftwareEngineering",
            "#SelfGrowth",
            "#TechCommunity",
        ]
    elif "ai" in cat_lower:
        cat_badge = "[AI & Emerging Technologies]"
        hashtags = [
            "#ArtificialIntelligence",
            "#MachineLearning",
            "#AITechnologies",
            "#TechInnovation",
            "#SoftwareEngineering",
            "#SelfGrowth",
            "#TechCommunity",
        ]
    elif "web" in cat_lower or "javascript" in cat_lower:
        cat_badge = "[Web Development]"
        hashtags = [
            "#WebDevelopment",
            "#Frontend",
            "#JavaScript",
            "#ReactJS",
            "#SoftwareEngineering",
            "#SelfGrowth",
            "#TechCommunity",
        ]
    else:
        cat_badge = "[Computer Science Engineering]"
        hashtags = [
            "#ComputerScience",
            "#SoftwareEngineering",
            "#TrendingTech",
            "#FullStackDevelopment",
            "#SelfGrowth",
            "#TechCommunity",
        ]

    hashtags_str = " ".join(hashtags)

    # Human-formatted LinkedIn Post (Rich, engaging, professional)
    linkedin_caption = f"""🚀 {cat_badge}: {title}

As software engineers and full-stack developers, staying ahead of modern computer science practices, system architecture, and tech trends is key to building high-performance applications.

💡 Key Takeaway:
{clean_desc if clean_desc else title}

🛠️ Core Engineering Takeaways:
• Optimize system performance, state management, and memory efficiency.
• Focus on clean code, security best practices, and scalable design patterns.
• Prevent technical debt and build robust applications.

What are your thoughts on this? How are you applying this in your projects? Drop your thoughts below! 👇

{hashtags_str}"""

    # Concise Twitter/X Tweet (<= 280 chars)
    short_title = title[:140]
    x_caption = f"🚀 {cat_badge}\n{short_title}\n\nKey Takeaway: {clean_desc[:65]}...\n\n{hashtags[0]} {hashtags[1]}"
    if len(x_caption) > 280:
        x_caption = f"🚀 {cat_badge}\n{short_title[:150]}...\n\n{hashtags[0]} {hashtags[1]}"


    post_data = {
        "caption": linkedin_caption,
        "x_caption": x_caption,
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

    print(f"Auto-generated human-styled linkedin_post.json ({len(linkedin_caption)} chars) and image_prompt.txt")


if __name__ == "__main__":
    main()
