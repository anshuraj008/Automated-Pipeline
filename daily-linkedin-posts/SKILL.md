---
name: daily-tech-post
description: Antigravity workflow for Full Stack Development, DSA, and AI updates.
---

# Daily Technical Post Pipeline

This repository automates high-value technical posts across three core pillars:
1. **Full Stack & Web Development** (React/Next.js, Node.js, Web Performance, System Architecture)
2. **Data Structures & Algorithms (DSA)** (LeetCode patterns, Data Structures, Big-O trade-offs)
3. **AI & Tech Trends** (Breaking AI releases, developer APIs, tech ecosystem news)


## Required run order

1. Fetch fresh sources:
   `python3 fetch_ai_news_rss.py`
2. Read `ai_news_data.json`. Prefer items published within 72 hours; never
   describe an older item as breaking news.
3. Select one story with a named source, a verifiable date, and a clear
   consequence. If the feeds are weak, report that honestly instead of padding.
4. Antigravity writes `linkedin_post.json` with one caption, source URL, and
   headline, then writes `image_prompt.txt`.
5. Read `image_prompt.txt` and generate exactly one visual with Antigravity.
   Do not use the old HTML, carousel, infographic, stock-photo, or spreadsheet
   generators.
6. Host the resulting 1080x1080 image at a public HTTPS URL.
7. Validate the Antigravity output and build one schedule entry:
   `python3 validate_antigravity_output.py`
   `python3 build_schedule.py --target both --image-url <PUBLIC_URL>`
8. Preview it:
   `python3 schedule_via_buffer.py --schedule-file schedule.json --dry-run`
9. Only after the preview is correct, schedule it:
   `python3 schedule_via_buffer.py --schedule-file schedule.json`

The normal one-command equivalent is:

```bash
python3 run_pipeline.py --image-url <PUBLIC_URL> --live
```

If the image is generated after the script starts, run the build and schedule
steps manually with its public URL. There must be exactly one `posts` item in
`schedule.json`.

## Antigravity image quality brief

The image must explain the selected AI update at a glance, not decorate it.
Use a square 1080x1080 editorial composition with one visual idea: a comparison,
timeline, process flow, system diagram, or hero statistic. Use a dark charcoal
or near-black background, one controlled accent color, high-contrast modern
sans-serif type, strong hierarchy, generous negative space, and 2-4 short
labels maximum. Include only verified numbers and a small source footer.

Reject outputs that look like Excel, a generic AI robot poster, a noisy
dashboard, a stock-photo collage, a dense text wall, a random icon grid, or
an unstructured “AI” graphic. Antigravity must check spelling, alignment,
contrast, margins, and mobile readability before returning the final image.

## Safety checks

- One story, one caption, one image, one scheduled post.
- Caption is <=280 characters because the same post is sent to LinkedIn and X.
- No personal-project references, personal work claims, engagement bait,
  invented facts, unsupported predictions, or stale “latest” language.
- No post is scheduled until the dry-run output is inspected.
