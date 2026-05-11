import requests
import feedparser
from datetime import date, timedelta
import os
import sys
import html
import re

SEARCH_KEYWORD = "nickelate"
SUPERCONDUCTIVITY_KEYWORD = "superconductivity"
TIME_RANGE_DAYS = 7
CATEGORY1 = "cond-mat.supr-con"
CATEGORY2 = "cond-mat.str-el"
MAX_RESULTS = 50
OUTPUT_FILE = "nickelate_superconductivity_recent_papers.md"

def process_abstract(abstract):
    if not abstract:
        return abstract
    text = html.unescape(abstract)
    replacements = {
        'Î´': '\\delta',
        'âˆ†': '\\Delta',
        'Ã': '\\mu',
        'Ã—': '\\times',
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    text = re.sub(r'\$ ', '$', text)
    text = re.sub(r' \$', '$', text)
    text = re.sub(r'(?<![a-zA-Z])\$_(\d+)\$', r'$\\_\1$', text)
    return text

END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '
    f'AND abs:"{SUPERCONDUCTIVITY_KEYWORD}" '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '
    f'AND submittedDate:[{START_DATE.strftime("%Y%m%d")}0000 TO {END_DATE.strftime("%Y%m%d")}2359]'
)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

if __name__ == "__main__":
    try:
        print(f"正在检索 {START_DATE} 至 {END_DATE} 的 nickelate 超导相关论文...")
        response = requests.get(ARXIV_API_URL, params={
            "search_query": search_query,
            "start": 0,
            "max_results": MAX_RESULTS,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }, timeout=30)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"Feed 解析失败: {feed.bozo_exception}")

        paper_entries = feed.entries
        total_papers = len(paper_entries)

        markdown_content = f"# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
        markdown_content += f"> 最后更新时间：**{END_DATE}**\n"
        markdown_content += f"> 检索范围：过去 **{TIME_RANGE_DAYS}** 天\n"
        markdown_content += f"> 论文数量：**{total_papers}** 篇\n\n"
        markdown_content += "---\n\n"

        for index, paper in enumerate(paper_entries, 1):
            paper_title = paper.title.replace("\n", " ").strip()
            author_list = ", ".join([author.name for author in paper.authors[:5]])
            if len(paper.authors) > 5:
                author_list += " et al."
            submit_date = paper.published.split("T")[0]
            arxiv_link = paper.id
            abstract = process_abstract(paper.summary.replace("\n", " ").strip())

            markdown_content += f"## {index}. {paper_title}\n\n"
            markdown_content += f"- **提交日期**：{submit_date}\n"
            markdown_content += f"- **作者**：{author_list}\n"
            markdown_content += f"- **arXiv链接**：{arxiv_link}\n\n"
            markdown_content += f"### 摘要\n${abstract}$\n\n"
            markdown_content += "---\n\n"

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✓ 成功生成文件：{OUTPUT_FILE}")
        print(f"📄 共处理 {total_papers} 篇论文")

    except Exception as e:
        print(f"✗ 运行出错：{str(e)}")
        sys.exit(1)