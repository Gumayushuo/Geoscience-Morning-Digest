# scripts/generate_digest.py
import os
import json
from datetime import datetime
from openai import OpenAI

# -------------------
DAILY_MD_PATH = "output/daily.md"
SEEN_JSON_PATH = "state/seen.json"

today = datetime.now().strftime("%Y-%m-%d")

# -------------------
# 读取记录
if not os.path.exists(SEEN_JSON_PATH):
    print("seen.json 不存在，请先抓取 RSS。")
    exit(1)

with open(SEEN_JSON_PATH, "r", encoding="utf-8") as f:
    seen = json.load(f)

# 严格筛选今日新增
papers_data = [p for p in seen if isinstance(p, dict) and p.get("date") == today]

if not papers_data:
    print("今日没有新增论文。")
    digest_text = "今日没有新增论文。"
else:
    # -------------------
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")
    
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    
    # 构建输入
    papers_brief = "\n".join([f"{p.get('title','未知标题')} ({p.get('source','未知期刊')})" for p in papers_data])
    
    system_prompt = (
        "你是一名地球科学领域科研助手。\n"
        "请根据以下论文列表生成 Markdown 格式的日报。\n"
        "要求：\n"
        "1. 整体趋势提炼，6-8点。\n"
        "2. 按主题自动分类，表格形式：主题 | 代表论文 | 备注。\n"
        "3. 每篇论文一句话核心贡献。\n"
        "4. 输出清晰 Markdown，保留 AI 输出的所有三部分，不要只截取部分。\n"
        "5. 不要包含原始条目列表。"
    )

    user_prompt = f"今天日期：{today}\n新增论文列表：\n{papers_brief}"

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
        ai_content = resp.choices[0].message.content
    except Exception as e:
        ai_content = f"摘要生成失败: {e}"

    digest_text = ai_content.strip()

# -------------------
# 构建 Markdown
md_content = f"# Daily Paper Digest — {today}\n\n"
md_content += f"**今日新增论文**：{len(papers_data)}\n\n"
md_content += "**摘要整理**：\n\n"
md_content += f"{digest_text}\n\n"

# -------------------
# 附录：原始文章信息
if papers_data:
    md_content += "---\n"
    md_content += "## 附录：原始文章信息\n\n"
    for i, p in enumerate(papers_data, 1):
        md_content += f"### {i}. {p.get('title','未知标题')}\n"
        md_content += f"- **作者**：{', '.join(p.get('authors',[])) if 'authors' in p else '未知'}\n"
        md_content += f"- **期刊/来源**：{p.get('source','未知')}\n"
        md_content += f"- **链接**：[原文]({p.get('link','')})\n"
        if p.get("summary"):
            md_content += f"- **摘要**：{p['summary']}\n"
        md_content += "\n"

# -------------------
# 写入文件
os.makedirs(os.path.dirname(DAILY_MD_PATH), exist_ok=True)
with open(DAILY_MD_PATH, "w", encoding="utf-8") as f:
    f.write(md_content)

print("Markdown 文件已更新。")
