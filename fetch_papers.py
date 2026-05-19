import requests
import feedparser
from datetime import date, timedelta

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
# 输出的Markdown文件名
OUTPUT_FILE = "nickelate_superconductivity_recent_papers.md"
# ==========================================================

# 计算日期范围
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=TIME_RANGE_DAYS)

# 构造arXiv API 搜索查询语句
# 规则：标题/摘要包含关键词 + 凝聚态物理分类 + 指定提交日期范围
search_query = (
    f'(ti:"{SEARCH_KEYWORD}" OR abs:"{SEARCH_KEYWORD}") '  # 标题/摘要含关键词（更合理）
    f'AND abs:"{SUPERCONDUCTIVITY_KEYWORD}" '
    f'AND (cat:{CATEGORY1} OR cat:{CATEGORY2}) '  # 括号包裹分类，确保逻辑分组
    f'AND submittedDate:[{START_DATE.strftime("%Y%m%d")}0000 TO {END_DATE.strftime("%Y%m%d")}2359]'
)

# arXiv API 官方接口地址
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# 构造API请求参数
request_params = {
    "search_query": search_query,
    "start": 0,
    "max_results": MAX_RESULTS,
    "sortBy": "submittedDate",  # 按提交时间排序
    "sortOrder": "descending"    # 最新的排在前面
}

if __name__ == "__main__":
    try:
        # 发送API请求
        print(f"正在检索 {START_DATE} 至 {END_DATE} 的相关论文...")
        response = requests.get(ARXIV_API_URL, params=request_params, timeout=30)
        response.raise_for_status()  # 捕获HTTP请求错误

        # 解析API返回的Atom格式数据
        feed = feedparser.parse(response.content)
        if feed.bozo:
            raise Exception(f"数据解析失败: {feed.bozo_exception}")
        
        paper_entries = feed.entries
        total_papers = len(paper_entries)

        if total_papers == 0:
            print(f"在指定时间范围内，未找到与{SEARCH_KEYWORD}相关的凝聚态物理论文")
            exit()

        # ===================== 生成Markdown格式内容 =====================
        markdown_content = f"# 凝聚态物理-镍酸盐高温超导相关论文\n\n"
        markdown_content += f"> 检索时间范围：**{START_DATE} 至 {END_DATE}**\n"
        markdown_content += f"> 共检索到 **{total_papers}** 篇相关论文，按提交时间降序排列\n\n"
        print(markdown_content)
        markdown_content += "---\n\n"

        # 遍历每篇论文，提取信息并格式化
        for index, paper in enumerate(paper_entries, 1):
            # 提取核心信息并处理换行、空格
            paper_title = paper.title.replace("\n", " ").strip()
            author_list = ", ".join([author.name for author in paper.authors])
            submit_date = paper.published.split("T")[0]  # 只保留日期，去掉时间
            arxiv_link = paper.id
            abstract = paper.summary.replace("\n", " ").strip()

            # 拼接Markdown内容
            markdown_content += f"## {index}. {paper_title}\n\n"
            markdown_content += f"- **提交日期**：{submit_date}\n"
            markdown_content += f"- **作者**：{author_list}\n"
            markdown_content += f"- **arXiv链接**：[{arxiv_link}]({arxiv_link})\n\n"
            markdown_content += f"### 摘要\n{abstract}\n\n"
            markdown_content += "---\n\n"

        # 输出结果
        # 1. 打印到控制台
        #print(markdown_content)
        # 2. 保存到Markdown文件
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"\n✅ 检索完成！结果已保存到当前目录的 {OUTPUT_FILE} 文件中")

    except Exception as e:
        print(f"❌ 运行出错：{str(e)}")
