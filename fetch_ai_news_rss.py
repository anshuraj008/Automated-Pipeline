import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from env_utils import new_ssl_context

ctx = new_ssl_context()

feeds = [
    # AI & Tech Trends
    {
        "source": "TechCrunch AI",
        "category": "AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "source": "VentureBeat AI",
        "category": "AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "source": "Wired AI",
        "category": "AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
    },
    {
        "source": "MIT Tech Review AI",
        "category": "AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    },
    # Full Stack & Web Development
    {
        "source": "Dev.to Web Dev",
        "category": "Full Stack & Web Dev",
        "url": "https://dev.to/feed/tag/webdev",
    },
    {
        "source": "Dev.to JavaScript",
        "category": "Full Stack & Web Dev",
        "url": "https://dev.to/feed/tag/javascript",
    },
    {
        "source": "Dev.to React",
        "category": "Full Stack & Web Dev",
        "url": "https://dev.to/feed/tag/react",
    },
    {
        "source": "Smashing Magazine",
        "category": "Full Stack & Web Dev",
        "url": "https://www.smashingmagazine.com/feed/",
    },
    {
        "source": "Hacker News Top",
        "category": "Tech & Full Stack",
        "url": "https://hnrss.org/frontpage?points=100",
    },
    # DSA & System Design
    {
        "source": "Dev.to DSA & Algorithms",
        "category": "DSA & System Design",
        "url": "https://dev.to/feed/tag/dsa",
    },
    {
        "source": "Dev.to Computer Science",
        "category": "DSA & System Design",
        "url": "https://dev.to/feed/tag/compsci",
    },
]


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

all_news = []
seen_urls = set()
cutoff = datetime.now(timezone.utc) - timedelta(days=7)

def find_first(elem, tags):
    for tag in tags:
        found = elem.find(tag)
        if found is not None:
            return found
    return None

for feed in feeds:
    print(f"Fetching RSS for {feed['source']}: {feed['url']}")
    req = urllib.request.Request(feed["url"], headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            rss_content = response.read()
            root = ET.fromstring(rss_content)

            # RSS <item> or Atom <entry>
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                if not items:
                    items = root.findall(".//entry")

            print(f"Found {len(items)} items in {feed['source']}")

            for item in items:
                title_el = find_first(item, ["title", "{http://www.w3.org/2005/Atom}title"])
                title = title_el.text if (title_el is not None and title_el.text) else ""

                link_el = find_first(item, ["link", "{http://www.w3.org/2005/Atom}link"])
                link = ""
                if link_el is not None:
                    link = link_el.text or link_el.attrib.get("href", "")

                desc_el = find_first(
                    item,
                    [
                        "description",
                        "summary",
                        "{http://www.w3.org/2005/Atom}summary",
                        "content",
                        "{http://www.w3.org/2005/Atom}content",
                    ],
                )
                desc_html = desc_el.text if (desc_el is not None and desc_el.text) else ""

                pub_el = find_first(
                    item,
                    [
                        "pubDate",
                        "published",
                        "updated",
                        "{http://www.w3.org/2005/Atom}published",
                        "{http://www.w3.org/2005/Atom}updated",
                    ],
                )
                pub_date = pub_el.text if (pub_el is not None and pub_el.text) else ""

                # Clean description
                clean_desc = ""
                if desc_html:
                    decoded = html.unescape(desc_html)
                    # Strip HTML tags
                    text_with_newlines = re.sub(r"<(?:p|br|div)[^>]*>", "\n", decoded)
                    clean_desc = re.sub(r"<[^>]+>", "", text_with_newlines)
                    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

                if not title.strip():
                    continue

                news_item = {
                    "source": feed["source"],
                    "category": feed.get("category", "General Tech"),
                    "title": title.strip(),
                    "description": clean_desc,
                    "pubDate": pub_date,
                    "url": link.strip(),
                }

                if link.strip() and link.strip() in seen_urls:
                    continue
                if link.strip():
                    seen_urls.add(link.strip())
                all_news.append(news_item)
    except Exception as e:
        print(f"Error fetching {feed['source']}: {e}")

# Keep the freshest items first and avoid stale feed backlog.
def parse_pub_date(value):
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except (TypeError, ValueError):
            return datetime.min.replace(tzinfo=timezone.utc)


all_news = [
    item for item in all_news
    if parse_pub_date(item["pubDate"]) >= cutoff
]
all_news.sort(key=lambda item: parse_pub_date(item["pubDate"]), reverse=True)

# Save to ai_news_data.json
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_news_data.json")
with open(out_path, "w") as f:
    json.dump(all_news, f, indent=2)

print(f"Saved {len(all_news)} news items to {out_path}")
if len(all_news) == 0:
    print("WARNING: Zero AI news items fetched!")
    raise SystemExit(1)
