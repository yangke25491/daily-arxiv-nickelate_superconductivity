import requests
import feedparser
from datetime import date, timedelta
import os
import sys
import time
import random

# ===================== 配置区域 =====================
SEARCH_KEYWORD = "nickelate"
SUPERCONDUCTIVITY_KEYWORD = "superconductivity"
TIME_RANGE_DAYS = 7
CATEGORY1 = "cond-mat.supr-con"
CATEGORY2 = "cond-mat.str-el"
MAX_RESULTS = 50
OUTPUT_FILE = "nickelate_superconductivity_recent_papers.md"
# ====================================================

END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '
    f'AND abs:"{SUPERCONDUCTIVITY_KEYWORD}" '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '
    f'AND submittedDate:[{START_DATE.strftime("%Y%m%d")}0000 TO {END_DATE.strftime("%Y%m%d")}2359]'
)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

request_params = {
    "search_query": search_query,
    "start": 0,
    "max_results": MAX_RESULTS,
    "sortBy": "submittedDate",
    "sortOrder": "descending"
}


def fetch_with_retry(url, params, max_retries=5):
    """Fetch URL with 3s delay + exponential backoff on 429 errors."""
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
        print(f"正在检索 {START_DATE} 至 {END_DATE} 的论文...")
        response = fetch_with_retry(ARXIV_API_URL, request_params)
        response.raise_for_status()
        print(f"HTTP 状态码: {response.status_code}")

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"Feed 解析失败: {feed.bozo_exception}")

        paper_entries = feed.entries
        total_papers = len(paper_entries)
        print(f"获取到论文数量: {total_papers}")

        katex_header = """<!-- KaTeX for LaTeX rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {
    renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\\\(', right: '\\\\)', display: false},
            {left: '\\\\[', right: '\\\\]', display: true}
        ],
        throwOnError: false
    });
});
</script>

"""

        markdown_content = katex_header
        markdown_content += f"# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
        markdown_content += f"> 最后更新时间：**{END_DATE}**\n"
        markdown_content += f"> 检索范围：过去 **{TIME_RANGE_DAYS}** 天\n"
        markdown_content += f"> 论文数量：**{total_papers}** 篇\n\n"
        markdown_content += "---\n\n"

        for index, paper in enumerate(paper_entries, 1):
            paper_title = paper.title.replace("\n", " ").strip()
            author_list = ", ".join([author.name for author in paper.authors])
            submit_date = paper.published.split("T")[0]
            arxiv_link = paper.id
            abstract = paper.summary.replace("\n", " ").strip()

            markdown_content += f"## {index}. {paper_title}\n\n"
            markdown_content += f"- **提交日期**：{submit_date}\n"
            markdown_content += f"- **作者**：{author_list}\n"
            markdown_content += f"- **arXiv链接**：{arxiv_link}\n\n"
            markdown_content += f"### 摘要\n<span class=\"abstract\">{abstract}</span>\n\n"
            markdown_content += "---\n\n"

        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✓ 成功生成文件：{OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"✗ 网络请求失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 运行出错：{str(e)}")
        sys.exit(1)
