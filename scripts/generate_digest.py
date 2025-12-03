# scripts/generate_digest.py
import os
import json
from datetime import datetime
from openai import OpenAI

# -------------------
SEEN_JSON_PATH = "state/seen.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

# -------------------
# 读取已抓取的论文
if not os.path.exists(SEEN_JSON_PATH):
    print("seen.json 不存在，请先运行 rss_reader.py 抓取论文。")
    exit(1)

with open(SEEN_JSON_PATH, "r", encoding="utf-8") as f:
    seen_data = json.load(f)

# 筛选今日新增论文
papers_data = [p for p in seen_data if isinstance(p, dict) and p.get("date") == TODAY]

# -------------------
if not papers_data:
    print(f"{TODAY} 没有新增论文。")
    digest_text = "今日没有新增论文。"
else:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        raise ValueError("请设置环境变量 DEEPSEEK_API_KEY 为 DeepSeek API Key")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # 构建简化列表给 AI
    papers_brief = "\n".join(
        [f"{p.get('title','未知标题')} ({p.get('source','未知期刊')})" for p in papers_data]
    )

    system_prompt = (
        "你是一名地球科学领域科研助手。\n"
        "请根据以下论文列表生成科研日报。\n"
        "要求：\n"
        "1. 整体趋势提炼，6-8点。\n"
        "2. 按主题自动分类，表格形式：主题 | 代表论文 | 备注。\n"
        "3. 每篇论文一句话核心贡献。\n"
        "4. 输出文本格式日报（不要 Markdown 格式化标记）。\n"
        "5. 不要包含原始条目列表。"
    )

    user_prompt = f"今天日期：{TODAY}\n新增论文列表：\n{papers_brief}"

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
        ai_content = resp.choices[0].message.content.strip()
    except Exception as e:
        ai_content = f"摘要生成失败: {e}"

    digest_text = ai_content

# -------------------
# 构建文本日报
today_header = f"Daily Paper Digest — {TODAY}\n"
summary_line = f"今日新增论文：{len(papers_data)}"
accum_line = f"已累计收录：{len(seen_data)} 篇\n"

email_content = f"{today_header}{summary_line}\n{accum_line}\n---\n\n"
email_content += f"摘要整理：\n{digest_text}\n\n"

# -------------------
# 附录：原始文章信息
if papers_data:
    email_content += "附录：原始文章信息\n"
    for i, p in enumerate(papers_data, 1):
        authors_list = [str(a) for a in p.get("authors", []) if a]
        authors_str = ", ".join(authors_list) if authors_list else "未知"
        email_content += f"\n{i}. {p.get('title','未知标题')}\n"
        email_content += f"   作者：{authors_str}\n"
        email_content += f"   来源：{p.get('source','未知')}\n"
        email_content += f"   链接：{p.get('link','')}\n"
        if p.get("summary"):
            email_content += f"   摘要：{p['summary']}\n"

# -------------------
# 输出到文本文件
OUTPUT_FILE = f"output/daily_{TODAY}.txt"
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(email_content)

print(f"日报已生成：{OUTPUT_FILE}")
