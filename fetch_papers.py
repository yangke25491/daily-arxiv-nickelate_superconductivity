import requests
import feedparser
from datetime import date, timedelta
import os
import sys

# ===================== 可自定义配置区 =====================
# 搜索关键词（镍酸盐）
SEARCH_KEYWORD = "nickelate"
SUPERCONDUCTIVITY_KEYWORD = "superconductivity"
# 时间范围：最近N天，默认30天（一个月）
TIME_RANGE_DAYS = 7
# arXiv分类：凝聚态物理全部分类，无需修改
CATEGORY1 = "cond-mat.supr-con"
CATEGORY2 = "cond-mat.str-el"
# 最大返回论文数量，避免结果过多
MAX_RESULTS =  50
# 输出的Markdown文件名
OUTPUT_FILE = "nickelate_superconductivity_recent_papers.md"
# ==========================================================

END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '  # 标题/摘要含关键词（更合理）
    f'AND abs:"{SUPERCONDUCTIVITY_KEYWORD}" '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '  # 括号包裹分类，确保逻辑分组
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

if __name__ == "__main__":
    try:
        print(f"正在检索 {START_DATE} 至 {END_DATE} 的论文...")
        print(f"请求 URL: {ARXIV_API_URL}")
        print(f"请求参数: {request_params}")

        response = requests.get(ARXIV_API_URL, params=request_params, timeout=30)
        print(f"HTTP 状态码: {response.status_code}")

        # 如果状态码不是 200，打印响应内容前 500 字符以便调试
        if response.status_code != 200:
            print(f"错误响应内容预览: {response.text[:500]}")
            response.raise_for_status()  # 这会抛出 HTTPError

        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"Feed 解析失败: {feed.bozo_exception}")

        paper_entries = feed.entries
        total_papers = len(paper_entries)
        print(f"获取到论文数量: {total_papers}")

        # ===================== 生成 Markdown =====================
        markdown_content = f"# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
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
            markdown_content += f"### 摘要\n{abstract}\n\n"
            markdown_content += "---\n\n"

        # ===================== 保存文件 =====================
        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"✅ 成功生成文件：{OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行出错：{str(e)}")
        sys.exit(1)

