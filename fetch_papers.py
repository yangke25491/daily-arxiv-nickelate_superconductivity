import requests
import feedparser
from datetime import date, timedelta
import os
import sys
import time
import random

SEARCH_KEYWORD = "nickelate"
SUPERCONDUCTIVITY_KEYWORD = "superconductivity"
TIME_RANGE_DAYS = 7
CATEGORY1 = "cond-mat.supr-con"
CATEGORY2 = "cond-mat.str-el"
MAX_RESULTS = 50
OUTPUT_FILE = "docs/index.md"

END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '
    f'AND (abs:"{SUPERCONDUCTIVITY_KEYWORD}") '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '
    f'AND submittedDate:[{START_DATE.strftime("%Y%m%d")}00 TO {END_DATE.strftime("%Y%m%d")}2359]'
)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

request_params = {
    "search_query": search_query,
    "start": 0,
    "max_results": MAX_RESULTS,
    "sortBy": "submittedDate",
    "sortOrder": "descending"
}


def kramdown_safe_abstract(text):
    """Convert $...$ to \(...\) for Kramdown, escape _ outside math."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == '$':
            j = i + 1
            while j < len(text) and text[j] != '$':
                j += 1
            if j < len(text):
                result.append('\\(' + text[i+1:j] + '\\)')
                i = j + 1
            else:
                result.append(text[i])
                i += 1
        else:
            if text[i] == '_':
                result.append('\\_')
            else:
                result.append(text[i])
            i += 1
    return ''.join(result)


def fetch_with_retry(url, params, max_retries=5):
    for attempt in range(max_retries):
        time.sleep(3)
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"[Attempt {attempt+1}] Rate limited (429), retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
        else:
            response.raise_for_status()
    response.raise_for_status()


if __name__ == "__main__":
    try:
        print(f"📚 {START_DATE} → {END_DATE} 论文更新...")
        response = fetch_with_retry(ARXIV_API_URL, request_params)

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"Feed 解析错误: {feed.bozo_exception}")

        paper_entries = feed.entries
        total_papers = len(paper_entries)
        print(f"共 {total_papers} 篇论文")

        markdown_content = "---
layout: default
---

"
        markdown_content += f"## 论文更新 (覆盖 {START_DATE} 至 {END_DATE} 期间)

"
        markdown_content += f"> 共 {total_papers} 篇论文
"
        markdown_content += f"> 关键词: **{SEARCH_KEYWORD}** & **{SUPERCONDUCTIVITY_KEYWORD}**

---
"

        for index, paper in enumerate(paper_entries, 1):
            paper_title = paper.title.replace("
", " ").strip()

            author_list = ", ".join([author.name for author in paper.authors])
            submit_date = paper.published.split("T")[0]
            arxiv_link = paper.id
            abstract = paper.summary.replace("
", " ").strip()
            abstract = kramdown_safe_abstract(abstract)

            markdown_content += f"### {index}. {paper_title}

"
            markdown_content += f"- **日期**: {submit_date}
"
            markdown_content += f"- **作者**: {author_list}
"
            markdown_content += f"- **arXiv**: {arxiv_link}

"
            markdown_content += f"#### 摘要
{abstract}

---
"

        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"OK: {OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"网络错误: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
