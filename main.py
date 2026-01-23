import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# --- 配置区域 ---
# 1. 关键词过滤 (只要文章包含这些词，就会被抓取)
KEYWORDS = ["UWB", "Ultra-Wideband", "Ultra Wideband", "FiRa", "802.15.4z", "High precision location"]

# 2. RSS 源列表 (通用 IoT 新闻)
RSS_FEEDS = [
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    "https://www.eetimes.com/designline/internet-of-things-designline/feed/"
]

# 3. 专门处理无RSS的官网 (以 FiRa 为例)
# 这里演示如何直接从网页“扣”新闻
def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    headers = {'User-Agent': 'Mozilla/5.0'}
    news_items = []
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 注意：这里的 class 名需要根据官网实际结构调整，以下是基于通用结构的示例
        # 假设新闻都在 <h3> 或 <div class="news-item"> 里
        # 这里为了演示稳定性，我们模拟一条“置顶”数据，实际需根据 F12 审查元素调整
        news_items.append({
            'title': "【监控】FiRa 官网最新动态 (请检查官网)",
            'link': url,
            'source': 'FiRa Consortium',
            'date': datetime.now()
        })
    except Exception as e:
        print(f"FiRa 抓取失败: {e}")
    return news_items

# --- 核心逻辑 ---

def check_keywords(text):
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def generate_newsletter():
    articles = []

    # 1. 处理 RSS 源
    print("正在抓取 RSS 源...")
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]: # 每个源只看最新的10条
            content_to_check = entry.title + " " + entry.get('summary', '')
            if check_keywords(content_to_check):
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'source': feed.feed.get('title', 'Unknown Source'),
                    'date': entry.get('published_parsed', datetime.now().timetuple())
                })

    # 2. 处理手动爬虫 (FiRa)
    print("正在抓取 FiRa...")
    articles.extend(scrape_fira_news())

    # 3. 生成 HTML
    # 简单的 CSS 美化
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>UWB 每日行业情报</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            .date {{ color: #666; font-size: 0.9em; margin-bottom: 30px; }}
            .card {{ background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            .tag {{ background: #e3f2fd; color: #007bff; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
            a {{ text-decoration: none; color: #2c3e50; font-size: 1.1em; font-weight: 600; }}
            a:hover {{ color: #007bff; }}
            .source {{ color: #888; font-size: 0.9em; margin-top: 5px; display: block; }}
        </style>
    </head>
    <body>
        <h1>📡 UWB & IoT 每日情报站</h1>
        <p class="date">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        {'<p>今日暂无相关新闻更新。</p>' if not articles else ''}
    """
    
    for art in articles:
        html_template += f"""
        <div class="card">
            <span class="tag">UWB/IoT</span>
            <div style="margin-top: 8px;">
                <a href="{art['link']}" target="_blank">{art['title']}</a>
                <span class="source">来源: {art['source']}</span>
            </div>
        </div>
        """
        
    html_template += "</body></html>"

    # 写入 index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("完成！index.html 已生成。")

if __name__ == "__main__":
    generate_newsletter()