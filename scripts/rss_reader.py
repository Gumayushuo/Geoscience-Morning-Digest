# rss_reader.py
import feedparser
import json
import os
from datetime import datetime

# -------------------
RSS_FEEDS = [
    "http://www.nature.com/nature/current_issue/rss",
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
    "https://www.nature.com/ngeo.rss",
    "https://www.nature.com/ncomms.rss",
    "https://www.nature.com/natrevearthenviron.rss",
    "https://www.pnas.org/action/showFeed?type=searchTopic&taxonomyCode=topic&tagCode=earth-sci",
    "https://www.annualreviews.org/rss/content/journals/earth/latestarticles?fmt=rss",
    "https://rss.sciencedirect.com/publication/science/00128252",
    "https://rss.sciencedirect.com/publication/science/0012821X",
    "https://agupubs.onlinelibrary.wiley.com/feed/19448007/most-recent",
    "https://agupubs.onlinelibrary.wiley.com/feed/21699356/most-recent",
    "https://agupubs.onlinelibrary.wiley.com/feed/15252027/most-recent",
    "https://rss.sciencedirect.com/publication/science/00167037"
]

SEEN_FILE = "state/seen.json"

today = datetime.now().strftime("%Y-%m-%d")

# -------------------
# 读取已有 seen.json
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            seen = json.load(f)
    except Exception:
        seen = []
else:
    seen = []

# 用 set 来快速检查已抓取的链接或 ID
seen_ids = set()
for entry in seen:
    uid = entry.get("id") or entry.get("link")
    if uid:
        seen_ids.add(uid)

new_entries = []

# -------------------
# 遍历 RSS 抓取新条目
for feed_url in RSS_FEEDS:
    print(f"抓取 RSS：{feed_url}")
    feed = feedparser.parse(feed_url)
    source_name = feed.feed.get("title", "未知来源")
    for entry in feed.entries:
        uid = entry.get("id") or entry.get("link")
        if not uid or uid in seen_ids:
            continue

        authors_list = []
        if "authors" in entry:
            for a in entry["authors"]:
                name = a.get("name") or ""
                if name:
                    authors_list.append(name)

        new_entry = {
            "id": uid,
            "title": entry.get("title", "未知标题"),
            "link": entry.get("link", ""),
            "source": source_name,
            "summary": entry.get("summary", "").strip(),
            "authors": authors_list,
            "date": today
        }

        seen.append(new_entry)
        seen_ids.add(uid)
        new_entries.append(new_entry)

print(f"本次抓取新论文数量：{len(new_entries)}")
print(f"累计论文总数：{len(seen)}")

# -------------------
# 保存 seen.json
os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
with open(SEEN_FILE, "w", encoding="utf-8") as f:
    json.dump(seen, f, ensure_ascii=False, indent=2)

print(f"seen.json 已更新：{SEEN_FILE}")
