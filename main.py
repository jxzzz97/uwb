import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- 配置区域 ---
KEYWORDS = ["UWB", "Ultra-Wideband", "Ultra Wideband", "FiRa", "802.15.4z", "High precision location"]

RSS_FEEDS = [
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    "https://www.eetimes.com/designline/internet-of-things-designline/feed/"
]

# --- 辅助功能：清洗摘要 ---
def clean_summary(html_text):
    if not html_text:
        return "暂无详细摘要，请点击标题查看原文。"
    
    # 1. 使用 BeautifulSoup 去除 HTML 标签 (如 <p>, <div>, <img>)
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(separator=' ')
    
    # 2. 去除多余的空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. 截取前 120 个字符 (约 50-80 个汉字或英文单词)
    if len(text) > 120:
        return text[:120] + "..."
    return text

# --- 核心逻辑 ---
def check_keywords(text):
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def scrape_fira_news():
    # 这里的代码针对 FiRa 官网，目前还是模拟数据
    # 真实抓取需要根据官网结构定制
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    return [{
        'title': "【FiRa 官网动态】请点击查看最新联盟新闻",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now(),
        'summary': "FiRa 联盟官方新闻发布页，点击直达官网查看最新的标准制定与合作动态。"
    }]

def generate_newsletter():
    articles = []

    # 1. 处理 RSS 源
    print("正在抓取 RSS 源...")
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                # 组合标题和摘要来检查关键词
                summary_raw = entry.get('summary', entry.get('description', ''))
                content_to_check = entry.title + " " + summary_raw
                
                if check_keywords(content_to_check):
                    # 提取并清洗摘要
                    clean_sum = clean_summary(summary_raw)
                    
                    articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'source': feed.feed.get('title', 'Unknown Source'),
                        'date': entry.get('published_parsed', datetime.now().timetuple()),
                        'summary': clean_sum  # 新增摘要字段
                    })
        except Exception as e:
            print(f"源 {url} 读取失败: {e}")

    # 2. 处理 FiRa
    articles.extend(scrape_fira_news())

    # 3. 按时间倒序排列 (最新的在最前)
    # 注意：这里做了一个简单的去重处理，防止同一篇文章出现两次
    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
    
    # 如果RSS里的日期格式不对，可能会导致排序报错，这里加个保险
    try:
        unique_articles.sort(key=lambda x: x['date'], reverse=True)
    except:
        pass # 如果排序失败就保持原样

    # 4. 生成 HTML
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UWB 每日行业情报</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #007bff; padding-bottom: 10px; font-size: 1.8rem; }}
            .date {{ color: #666; font-size: 0.9em; margin-bottom: 30px; }}
            
            .card {{ 
                background: white; 
                padding: 24px; 
                margin-bottom: 20px; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
                transition: transform 0.2s; 
                border-left: 5px solid #007bff;
            }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
            
            .tag {{ background: #e3f2fd; color: #007bff; padding: 4px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
            .source {{ color: #999; font-size: 0.85em; margin-left: 10px; }}
            
            a.title-link {{ 
                text-decoration: none; 
                color: #2c3e50; 
                font-size: 1.25em; 
                font-weight: 700; 
                display: block; 
                margin-top: 12px; 
                margin-bottom: 8px;
                line-height: 1.4;
            }}
            a.title-link:hover {{ color: #007bff; }}
            
            .summary {{ 
                color: #555; 
                font-size: 0.95em; 
                line-height: 1.6; 
                margin: 0; 
            }}
            
            .footer {{ margin-top: 50px; text-align: center; color: #aaa; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <h1>📡 UWB & IoT 每日情报站</h1>
        <p class="date">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        {'<div class="card"><p>今日暂无相关新闻更新。</p></div>' if not unique_articles else ''}
    """
    
    for art in unique_articles:
        html_template += f"""
        <div class="card">
            <div>
                <span class="tag">News</span>
                <span class="source">{art['source']}</span>
            </div>
            <a href="{art['link']}" class="title-link" target="_blank">{art['title']}</a>
            <p class="summary">{art['summary']}</p>
        </div>
        """
        
    html_template += """
        <div class="footer">
            Powered by GitHub Actions | Auto-generated daily
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("完成！index.html 已生成。")

if __name__ == "__main__":
    generate_newsletter()
