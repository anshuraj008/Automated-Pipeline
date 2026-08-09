import argparse
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
NEWS_PATH = os.path.join(PROJECT_ROOT, "ai_news_data.json")
POST_PATH = os.path.join(PROJECT_ROOT, "linkedin_post.json")
PROMPT_PATH = os.path.join(PROJECT_ROOT, "image_prompt.txt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-index", type=int, default=3, help="Index of news item in ai_news_data.json")
    args = parser.parse_args()

    if not os.path.exists(NEWS_PATH):
        print(f"Error: {NEWS_PATH} not found. Run fetch_ai_news_rss.py first.")
        sys.exit(1)

    with open(NEWS_PATH, "r", encoding="utf-8") as f:
        news_items = json.load(f)

    # Filter English stories only
    valid_stories = []
    for item in news_items:
        t = item.get("title", "")
        if t and (sum(1 for c in t if ord(c) < 128) / len(t)) > 0.8:
            valid_stories.append(item)

    if not valid_stories:
        valid_stories = news_items

    idx = args.story_index if 0 <= args.story_index < len(valid_stories) else 0
    top_story = valid_stories[idx]
    title = top_story.get("title", "").strip()
    source_url = top_story.get("url", "").strip()
    source = top_story.get("source", "Tech Update").strip()
    category = top_story.get("category", "Full Stack & Web Dev").strip()
    description = top_story.get("description", "").strip()

    clean_desc = description.replace("\n", " ").strip()
    if clean_desc.lower().startswith(title.lower()):
        clean_desc = clean_desc[len(title):].strip()
    if clean_desc.lower().startswith("description:"):
        clean_desc = clean_desc[len("description:"):].strip()
    if clean_desc.lower().startswith(title.lower()):
        clean_desc = clean_desc[len(title):].strip()

    full_linkedin_desc = clean_desc
    if len(full_linkedin_desc) > 350:
        full_linkedin_desc = full_linkedin_desc[:350] + "..."

    # Determine CS Engineering Category Tag & Hashtags
    cat_lower = (category + " " + title).lower()
    if "ai" in cat_lower or "claude" in cat_lower or "agent" in cat_lower or "llm" in cat_lower:
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
    elif "full stack" in cat_lower or "react" in cat_lower or "node" in cat_lower:
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
{full_linkedin_desc if full_linkedin_desc else title}

🛠️ Core Engineering Takeaways:
• Optimize system performance, state management, and memory efficiency.
• Focus on clean code, security best practices, and scalable design patterns.
• Prevent technical debt and build robust applications.

What are your thoughts on this? How are you applying this in your projects? Drop your thoughts below! 👇

{hashtags_str}"""

    # Complete Twitter/X Tweet (<= 280 chars, complete sentences without mid-word truncation)
    summary_for_x = clean_desc
    if len(summary_for_x) > 110:
        match = re.search(r'[^.!?]*[.!?]', summary_for_x[:110])
        if match and match.end() > 20:
            summary_for_x = summary_for_x[:match.end()].strip()
        else:
            space_idx = summary_for_x[:100].rfind(' ')
            if space_idx > 30:
                summary_for_x = summary_for_x[:space_idx].strip() + "."
            else:
                summary_for_x = summary_for_x[:90].strip()

    x_hashtags = f"{hashtags[0]} {hashtags[1]}" if len(hashtags) >= 2 else "#SoftwareEngineering"

    x_caption = f"🚀 {cat_badge}\n{title}\n\n💡 {summary_for_x}\n\n{x_hashtags}"

    if len(x_caption) > 280:
        max_t_len = 280 - len(f"🚀 {cat_badge}\n\n\n\n{x_hashtags}")
        x_caption = f"🚀 {cat_badge}\n{title[:max_t_len]}\n\n{x_hashtags}"

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

    print(f"Auto-generated human-styled linkedin_post.json ({len(linkedin_caption)} chars, X: {len(x_caption)} chars) and image_prompt.txt for story index {idx}")


if __name__ == "__main__":
    main()
