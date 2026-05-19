import requests
import feedparser
import re
from datetime import date, timedelta
import os

# ===================== 可自定义配置区 =====================
# 搜索关键词（镍酸盐）
SEARCH_KEYWORD = "nickelate"
SUPERCONDUCTIVITY_KEYWORD = "superconductivity"
# 时间范围：最近N天，默认30天（一个月）
TIME_RANGE_DAYS = 30
# arXiv分类：凝聚态物理全部分类，无需修改
CATEGORY1 = "cond-mat.supr-con"
CATEGORY2 = "cond-mat.str-el"
# 最大返回论文数量，避免结果过多
MAX_RESULTS = 100
# 输出的Markdown文件名（优先使用环境变量）
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "nickelate_superconductivity_recent_papers.md")
# ===========================================================

def escape_underscores_for_latex(text):
    """转义LaTeX数学表达式前的下划线，防止Kramdown误解析为斜体"""
    return re.sub(r'(?<!\\)\$_', r'\$_', text)

# 计算日期范围
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

# 构造arXiv API 搜索查询语句
search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '
    f'AND abs:"{SUPERCONDUCTIVITY_KEYWORD}" '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '
    f'AND submittedDate:[{START_DATE.strftime("%Y%m%d")}0000 TO {END_DATE.strftime("%Y%m%d")}2359]'
)

# arXiv API 官方接口地址
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# 构造API请求参数
request_params = {
    "search_query": search_query,
    "start": 0,
    "max_results": MAX_RESULTS,
    "sortBy": "submittedDate",
    "sortOrder": "descending"
}

if __name__ == "__main__":
    try:
        print(f"正在检索 {START_DATE} 至 {END_DATE} 的相关论文...")
        response = requests.get(ARXIV_API_URL, params=request_params, timeout=30)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"数据解析失败: {feed.bozo_exception}")

        paper_entries = feed.entries
        total_papers = len(paper_entries)

        if total_papers == 0:
            print(f"在指定时间范围内，未找到与{SEARCH_KEYWORD}相关的凝聚态物理论文")
            exit()

        markdown_content = f"# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
        markdown_content += f"> 检索时间范围：**{START_DATE} 至 {END_DATE}**\n"
        markdown_content += f"> 数据检索到 **{total_papers}** 篇相关论文，按提交时间降序排列\n\n"
        markdown_content += "---\n\n"

        for index, paper in enumerate(paper_entries, 1):
            paper_title = escape_underscores_for_latex(paper.title.replace("\n", " ").strip())
            author_list = ", ".join([author.name for author in paper.authors])
            submit_date = paper.published.split("T")[0]
            arxiv_link = paper.id
            abstract = escape_underscores_for_latex(paper.summary.replace("\n", " ").strip())

            markdown_content += f"## {index}. {paper_title}\n\n"
            markdown_content += f"- **提交日期**：{submit_date}\n"
            markdown_content += f"- **作者**：{author_list}\n"
            markdown_content += f"- **arXiv链接**：[{arxiv_link}]({arxiv_link})\n\n"
            markdown_content += f"### 摘要\n{abstract}\n\n"
            markdown_content += "---\n\n"

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"\n✅ 检索完成！结果已保存到当前目录的 {OUTPUT_FILE} 文件中")

    except Exception as e:
        print(f"❌ 运行出错：{str(e)}")
