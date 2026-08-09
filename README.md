# AI News Scheduler & Buffer Automated Pipeline

This repository automatically fetches recent AI, Computer Science, and Software Engineering news, formats rich engaging updates for LinkedIn and concise complete posts for X (Twitter), and schedules them through the Buffer API.

---

## 🚀 Quick Running Commands (Terminal & PowerShell)

### 1. Complete Full Pipeline (Fetch + Generate + Schedule Live)
Fetches the latest news feeds, formats post content for the top story, and schedules it live to Buffer:
```powershell
uv run python fetch_ai_news_rss.py; uv run python auto_generate_post.py; uv run python run_pipeline.py --live
```

### 2. Schedule Current Post Live
Schedules the existing `linkedin_post.json` directly to Buffer:
```powershell
uv run python run_pipeline.py --live
```

### 3. Preview Only (Dry Run)
Validates content and previews Buffer schedule without actually posting:
```powershell
uv run python run_pipeline.py
```

### 4. Select a Specific News Topic (by Index)
Generates content for a specific story index from `ai_news_data.json` (e.g. index 2) and schedules live:
```powershell
uv run python auto_generate_post.py --story-index 2; uv run python run_pipeline.py --live
```

---

## 🤖 100% Automated Cloud Execution (GitHub Actions)

The pipeline is set to run **automatically every day at 9:00 AM IST (03:30 UTC)** via [.github/workflows/daily_post.yml](file:///.github/workflows/daily_post.yml).

To enable hands-free daily automation:
1. Push this repository to GitHub.
2. Go to **Settings** -> **Secrets and variables** -> **Actions** in your GitHub repository.
3. Add the following 4 secrets from your `.env` file:
   - `BUFFER_API_KEY`
   - `BUFFER_ORG_ID`
   - `BUFFER_LINKEDIN_CHANNEL_ID`
   - `BUFFER_X_CHANNEL_ID`

---

## 🛠️ Setup & Environment

Python 3.10+ and `uv` package manager are recommended.

Place your Buffer API credentials in `.env`:

```env
BUFFER_API_KEY=your_buffer_api_key
BUFFER_ORG_ID=your_buffer_organization_id
BUFFER_LINKEDIN_CHANNEL_ID=your_linkedin_channel_id
BUFFER_X_CHANNEL_ID=your_x_channel_id
```

---

## 💡 Key Features & Smart Behaviors

- **Automatic Future Time Handling**: If today's target time (e.g. 9:00 AM IST) has already passed, the scheduler automatically shifts the publication date to tomorrow morning (`9:00 AM IST`), preventing Buffer API `dueAt` errors.
- **Un-truncated X Captions**: Twitter/X posts are formatted with complete sentences under 280 characters without mid-word cuts or `...` truncation.
- **Optional Image URL**: `--image-url` is optional in `run_pipeline.py`. If omitted, high-converting text-only posts are scheduled seamlessly.
- **English Language Filtering**: Automatically filters out non-English feed items during content generation.

---

## 📁 Repository File Structure

- `fetch_ai_news_rss.py`: Aggregates, deduplicates, and filters 7-day RSS technical feeds into `ai_news_data.json`.
- `auto_generate_post.py`: Creates structured LinkedIn and X post content in `linkedin_post.json` and visual prompts in `image_prompt.txt`.
- `validate_antigravity_output.py`: Ensures caption lengths and prompt requirements are satisfied before scheduling.
- `build_schedule.py`: Builds `schedule.json` for LinkedIn and X with auto-date IST calculation.
- `schedule_via_buffer.py`: Interacts with Buffer API for dry-run previews and live post creation.
- `run_pipeline.py`: Master runner orchestrating validation, schedule building, and Buffer submission.
- `.github/workflows/daily_post.yml`: GitHub Actions automated workflow for daily posting at 9:00 AM IST.
