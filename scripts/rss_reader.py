import feedparser
import json
import os
from datetime import datetime, timezone
import time

# -------------------
# Configuration
# -------------------
SEEN_JSON_PATH = "state/seen.json"
PAPERS_JSON_PATH = "output/papers.json"

# 地球科学相关 RSS 源列表
RSS_URLS = [
    "http://www.nature.com/nature/current_issue/rss",  #nature
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",  #science
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",   #SA
    "https://www.nature.com/ngeo.rss",     #NG
    "https://www.nature.com/ncomms.rss",   #NC
    "https://www.nature.com/natrevearthenviron.rss",   #Nature REE
    "https://www.nature.com/commsenv.rss",             #NC EE
    "https://www.pnas.org/action/showFeed?type=searchTopic&taxonomyCode=topic&tagCode=earth-sci", #PNAS
    "https://www.annualreviews.org/rss/content/journals/earth/latestarticles?fmt=rss", #Annual Review of Earth and Planetary Sciences
    "https://rss.sciencedirect.com/publication/science/00128252",   #ESR
    "https://rss.sciencedirect.com/publication/science/0012821X",   #EPSL
    "https://agupubs.onlinelibrary.wiley.com/feed/19448007/most-recent",  #GRL
    "https://agupubs.onlinelibrary.wiley.com/feed/15252027/most-recent",   #Geochemistry, Geophysics, Geosystems
    "https://agupubs.onlinelibrary.wiley.com/feed/21699356/most-recent",    #JGR:Solid Earth
    "https://rss.sciencedirect.com/publication/science/00167037",     #GCA
    "https://pubs.geoscienceworld.org/rss/site_65/advanceAccess_33.xml",   #Geology
    "https://pubs.geoscienceworld.org/rss/site_119/advanceAccess_60.xml",  #AM
    "https://pubs.geoscienceworld.org/economicgeology/issue/120/6",       #EG
    "https://pubs.geoscienceworld.org/rss/site_69/advanceAccess_35.xml", #GSAB
    "https://academic.oup.com/rss/site_5332/advanceAccess_3198.xml",     #NSR
    "https://agupubs.onlinelibrary.wiley.com/feed/19449194/most-recent",  #Tectonic
    "https://www.earthsciencefrontiers.net.cn/CN/rss_zxly_1005-2321.xml",#geoscience frontiers  地学前缘（英文版）
    "https://rss.sciencedirect.com/publication/science/01691368",   #OGR
]

def load_seen_papers():
    """Load the list of seen paper IDs from a JSON file."""
    if os.path.exists(SEEN_JSON_PATH):
        with open(SEEN_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                # 尝试加载整个列表，然后提取 ID 集合
                seen_list = json.load(f)
                return {p.get("id") for p in seen_list if isinstance(p, dict) and p.get("id")}, seen_list
            except json.JSONDecodeError:
                print("Warning: seen.json is corrupted or empty. Starting fresh.")
                return set(), []
    return set(), []

def save_seen_papers(seen_list):
    """Save the updated list of seen papers to a JSON file."""
    os.makedirs(os.path.dirname(SEEN_JSON_PATH), exist_ok=True)
    with open(SEEN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(seen_list, f, indent=2, ensure_ascii=False)

def parse_date(entry):
    """
    Attempts to parse the publication date from the RSS entry.
    
    Prioritizes published_parsed/updated_parsed, falls back to today's date.
    Returns date in 'YYYY-MM-DD' format.
    """
    try:
        # Use updated_parsed or published_parsed (struct_time format)
        date_struct = entry.get('updated_parsed') or entry.get('published_parsed')
        if date_struct:
            # Convert struct_time to datetime object and then format
            date_dt = datetime(*date_struct[:6], tzinfo=timezone.utc)
            return date_dt.strftime("%Y-%m-%d")
    except Exception as e:
        # If parsing fails, print a warning and fall back to today
        print(f"Warning: Failed to parse date for entry '{entry.get('title', 'Unknown')}'. Error: {e}")
        pass

    # Fallback to today's date (Local time zone)
    return datetime.now().strftime("%Y-%m-%d")

def fetch_new_entries():
    """Fetches new entries from all RSS feeds."""
    
    # ---- 关键修复：判断是否第一次运行 ----
    is_first_run = (not os.path.exists(SEEN_JSON_PATH)) or (os.path.getsize(SEEN_JSON_PATH) == 0)

    seen_ids, seen_list = load_seen_papers()
    new_entries_list = []
    
    print(f"Loaded {len(seen_ids)} existing paper IDs.")
    if is_first_run:
        print("🚨 检测到首次运行：将仅初始化数据库，不会推送任何历史论文。")

    for url in RSS_URLS:
        print(f"解析 RSS: {url}")
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get('title', url.split('/')[2])
            
            for entry in feed.entries:
                uid = entry.get("id") or entry.get("link")
                if not uid:
                    continue
                
                if uid in seen_ids:
                    continue

                # ---- 首次运行：只记录，不推送 ----
                if is_first_run:
                    seen_ids.add(uid)
                    seen_list.append({
                        "id": uid,
                        "title": entry.get('title',''),
                        "link": entry.get('link',''),
                        "authors": [a.get("name") for a in entry.get("authors", [])],
                        "summary": "",
                        "source": source_name,
                        "date": parse_date(entry),
                        "sent": True
                    })
                    continue

                # ---- 正常运行：新增论文 ----
                summary_raw = entry.get('summary') or entry.get('content', [{}])[0].get('value')
                summary_text = summary_raw.replace('<p>', '').replace('</p>', '').strip() if summary_raw else ""

                authors_list = [author.get('name') for author in entry.get('authors', [])]

                new_entry = {
                    "id": uid,
                    "title": entry.get('title','Unknown Title'),
                    "link": entry.get('link',''),
                    "authors": authors_list,
                    "summary": summary_text,
                    "source": source_name,
                    "date": parse_date(entry),
                    "sent": False
                }

                new_entries_list.append(new_entry)
                seen_ids.add(uid)

        except Exception as e:
            print(f"Error processing RSS feed {url}: {e}")

    # ---- 合并 seen_list，仅限非首次运行 ----
    if not is_first_run:
        current_ids = {p["id"] for p in new_entries_list}
        filtered_old = [p for p in seen_list if p.get("id") not in current_ids]
        seen_list = new_entries_list + filtered_old

    save_seen_papers(seen_list)
    
    return new_entries_list if not is_first_run else []


if __name__ == "__main__":
    new_papers = fetch_new_entries()
    
    print(f"共抓取 {len(new_papers)} 篇新论文")

    if new_papers:
        # Save new papers to a separate file (optional, but helpful for debugging/future features)
        os.makedirs(os.path.dirname(PAPERS_JSON_PATH), exist_ok=True)
        with open(PAPERS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(new_papers, f, indent=2, ensure_ascii=False)
        print(f"新论文详情已保存至 {PAPERS_JSON_PATH}")
    else:
        print("今日无新增论文。")
