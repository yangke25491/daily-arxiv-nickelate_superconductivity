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

def process_latex_math(text):
    """处理 arXiv 摘要中的 LaTeX 数学公式，使其兼容 Kramdown + KaTeX 渲染

    arXiv 使用 $...$ 作为行内数学公式定界符。
    Kramdown 将 { } 解析为内联属性列表（IAL），会吞掉公式中的花括号。
    本函数：
    1. 保留 $...$ 定界符（KaTeX 可识别）
    2. 对 $...$ 之外的花括号进行转义 \{ \}
    3. 对 $...$ 之外的下划线进行转义 \_
    """
    result = []
    # 分割文本：匹配 $...$ 数学公式块
    parts = re.split(r'(\$[^\$]+\$)', text)

    for part in parts:
        if part.startswith('$') and part.endswith('$') and len(part) > 1:
            # 数学公式内部：保持原样，KaTeX 会渲染
            result.append(part)
        else:
            # 非数学公式区域：转义花括号和下划线
            escaped = part.replace('{', '\\{').replace('}', '\\}').replace('_', '\\_')
            result.append(escaped)

    return ''.join(result)

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

        markdown_content = f"""---
layout: default
title: 镍酸盐超导论文 - {{END_DATE}}
---

# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
        markdown_content += f"> 检索时间范围：**{START_DATE} 至 {END_DATE}**\n"
        markdown_content += f"> 数据检索到 **{total_papers}** 篇相关论文，按提交时间降序排列\n\n"
        markdown_content += "---\n\n"

        for index, paper in enumerate(paper_entries, 1):
            paper_title = process_latex_math(paper.title.replace("\n", " ").strip())
            author_list = ", ".join([author.name for author in paper.authors])
            submit_date = paper.published.split("T")[0]
            arxiv_link = paper.id
            abstract = process_latex_math(paper.summary.replace("\n", " ").strip())

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
