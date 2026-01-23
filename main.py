import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

# --- 配置区域 ---
KEYWORDS = ["UWB", "Ultra-Wideband", "Ultra Wideband", "FiRa", "802.15.4z", "High precision location"]

RSS_FEEDS = [
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    "https://www.eetimes.com/designline/internet-of-things-designline/feed/"
]

# --- 辅助工具 ---
def clean_summary(html_text):
    if not html_text: return "暂无详细摘要。"
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) < 5: return "点击标题查看新闻详情 (原文包含多媒体内容)"
        if len(text) > 120: return text[:120] + "..."
        return text
    except:
        return html_text[:100] + "..."

def is_recent(entry_date_parsed):
    if not entry_date_parsed: return False
    try:
        news_date = datetime.fromtimestamp(time.mktime(entry_date_parsed))
        return (datetime.now() - news_date).days <= 7
    except:
        return False

def check_keywords(text):
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    return [{
        'title': "【FiRa 官网动态】请点击查看最新联盟新闻",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now().timetuple(),
        'summary': "FiRa 联盟官方新闻发布页，点击直达官网查看最新的标准制定与合作动态。"
    }]

# --- 核心生成逻辑 ---
def generate_newsletter():
    articles = []
    print("正在抓取并过滤旧新闻...")
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if not entry.get('published_parsed') or not is_recent(entry.get('published_parsed')):
                    continue 
                
                summary_raw = entry.get('summary', entry.get('description', ''))
                content_to_check = entry.title + " " + summary_raw
                
                if check_keywords(content_to_check):
                    articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'source': feed.feed.get('title', 'Unknown Source'),
                        'date': entry.get('published_parsed'),
                        'summary': clean_summary(summary_raw)
                    })
        except Exception as e:
            print(f"源 {url} 出错: {e}")

    articles.extend(scrape_fira_news())

    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
            
    unique_articles.sort(key=lambda x: time.mktime(x['date']) if x['date'] else 0, reverse=True)

    # 准备空状态的 HTML (为了避免 f-string 语法错误，我们把逻辑提出来)
    empty_html = ""
    if not unique_articles:
        empty_html = '<div class="empty-msg"><h3>📭</h3><p>过去 7 天内暂未监测到核心信息更新。</p></div>'

    # 生成 HTML
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tiagile - UWB & IoT 行业情报</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Poppins', -apple-system, sans-serif;
                margin: 0; padding: 0;
                background: linear-gradient(rgba(240, 242, 250, 0.85), rgba(240, 242, 250, 0.85)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
                background-size: cover; background-attachment: fixed; background-position: center;
                min-height: 100vh; display: flex; justify-content: center; align-items: center;
            }}
            .main-container {{
                width: 90%; max-width: 800px; margin: 40px 0; padding: 40px;
                background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border-radius: 24px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            .header-section {{ text-align: center; margin-bottom: 40px; }}
            h1 {{
                font-weight: 700; font-size: 2.2rem; margin-bottom: 10px;
                background: linear-gradient(135deg, #0061ff, #60efff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                display: inline-block;
            }}
            .date {{ color: #666; font-weight: 600; letter-spacing: 1px; }}
            .card {{
                background: rgba(255, 255, 255, 0.95); padding: 25px; margin-bottom: 25px;
                border-radius: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); transition: all 0.3s ease;
                border-left: 6px solid #0061ff;
            }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.1); }}
            .meta-info {{ display: flex; align-items: center; margin-bottom: 12px; }}
            .tag {{ background: linear-gradient(135deg, #0061ff, #60efff); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.7em; font-weight: 700; margin-right: 10px; }}
            .source {{ color: #888; font-size: 0.85em; font-weight: 600; }}
            a.title-link {{ text-decoration: none; color: #2c3e50; font-size: 1.3em; font-weight: 700; display: block; margin-bottom: 12px; line-height: 1.3; }}
            a.title-link:hover {{ color: #0061ff; }}
            .summary {{ color: #555; font-size: 0.95em; line-height: 1.6; margin: 0; }}
            .empty-msg {{ text-align: center; padding: 60px 20px; color: #888; }}
            .empty-msg h3 {{ color: #ccc; font-size: 3em; margin: 0 0 20px 0; }}
            .footer {{ margin-top: 60px; text-align: center; padding-top: 20px; border-top: 2px solid rgba(0,0,0,0.05); }}
            .tiagile-logo {{ font-size: 1.8rem; font-weight: 800; color: #2c3e50; letter-spacing: -1px; display: inline-block; }}
            .tiagile-logo span {{ color: #0061ff; }}
            .footer-note {{ color: #aaa; font-size: 0.8em; margin-top: 10px; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header-section">
                <h1>⚡️ UWB & IoT 行业情报站</h1>
                <p class="date">{datetime.now().strftime('%Y.%m.%d')} | Daily Briefing</p>
            </div>
            
            {empty_html}
    """
    
    for art in unique_articles:
        date_str = time.strftime('%m-%d', art['date']) if art['date'] else 'Recent'
        html_template += f"""
        <div class="card">
            <div class="meta-info">
                <span class="tag">NEWS</span>
                <span class="source">{art['source']} · {date_str}</span>
            </div>
            <a href="{art['link']}" class="title-link" target="_blank">{art['title']}</a>
            <p class="summary">{art['summary']}</p>
        </div>
        """
        
    html_template += """
            <div class="footer">
                <div class="tiagile-logo">T<span>i</span>agile</div>
                <p class="footer-note">Intelligence Powered by GitHub Actions</p>
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("完成！")

if __name__ == "__main__":
    generate_newsletter()
