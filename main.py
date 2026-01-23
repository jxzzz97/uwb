import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

# --- 配置区域 ---
# 关键词 (不区分大小写)
KEYWORDS = ["UWB", "Ultra-Wideband", "Ultra Wideband", "FiRa", "802.15.4z", "High precision location"]

# RSS 源列表
RSS_FEEDS = [
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    "https://www.eetimes.com/designline/internet-of-things-designline/feed/"
]

# --- 辅助工具 (保持不变) ---
def clean_summary(html_text):
    if not html_text: return "暂无详细摘要。"
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(separator=' ')
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < 5: return "点击标题查看新闻详情 (原文包含多媒体内容)"
    if len(text) > 120: return text[:120] + "..." # 稍微增加了一点字数
    return text

# 检查时间 (只保留最近 7 天的新闻)
def is_recent(entry_date_parsed):
    if not entry_date_parsed: return False
    news_date = datetime.fromtimestamp(time.mktime(entry_date_parsed))
    return (datetime.now() - news_date).days <= 7

def check_keywords(text):
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False

# 模拟 FiRa 官网抓取
def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    return [{
        'title': "【FiRa 官网动态】请点击查看最新联盟新闻",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now().timetuple(),
        'summary': "FiRa 联盟官方新闻发布页，点击直达官网查看最新的标准制定与合作动态。"
    }]

# --- 核心生成逻辑 (HTML模板大幅更新) ---
def generate_newsletter():
    articles = []
    print("正在抓取并过滤旧新闻...")
    
    # 1. 处理 RSS 源
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 时间过滤
                if not entry.get('published_parsed') or not is_recent(entry.get('published_parsed')):
                    continue 
                
                # 关键词过滤
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

    # 2. 加入 FiRa
    articles.extend(scrape_fira_news())

    # 3. 排序和去重
    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
            
    unique_articles.sort(key=lambda x: time.mktime(x['date']) if x['date'] else 0, reverse=True)

    # 4. 生成全新华丽版 HTML
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tiagile - UWB & IoT 行业情报</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            /* 全局设置 */
            body {{
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                color: #333;
                /* 设置背景图：这里使用了一个免费的科技感网络图片链接 */
                background: linear-gradient(rgba(240, 242, 250, 0.85), rgba(240, 242, 250, 0.85)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }}

            /* 主内容容器 (毛玻璃效果) */
            .main-container {{
                width: 90%;
                max-width: 800px;
                margin: 40px 0;
                padding: 40px;
                background: rgba(255, 255, 255, 0.75); /* 半透明白色 */
                backdrop-filter: blur(12px); /* 关键：毛玻璃模糊滤镜 */
                -webkit-backdrop-filter: blur(12px);
                border-radius: 24px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1), 0 5px 15px rgba(0,0,0,0.05);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            /* 标题区域 */
            .header-section {{ text-align: center; margin-bottom: 40px; }}
            h1 {{
                font-weight: 700;
                font-size: 2.2rem;
                margin-bottom: 10px;
                /* 标题渐变色 */
                background: linear-gradient(135deg, #0061ff, #60efff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
            }}
            .date {{ color: #666; font-weight: 600; letter-spacing: 1px; }}

            /* 卡片设计 */
            .card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                margin-bottom: 25px;
                border-radius: 16px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
                border-left: 6px solid #0061ff;
                position: relative;
                overflow: hidden;
            }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.1); }}
            
            /* 卡片内容细节 */
            .meta-info {{ display: flex; align-items: center; margin-bottom: 12px; }}
            .tag {{ background: linear-gradient(135deg, #0061ff, #60efff); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.7em; font-weight: 700; letter-spacing: 0.5px; margin-right: 10px; box-shadow: 0 2px 5px rgba(0,97,255,0.3); }}
            .source {{ color: #888; font-size: 0.85em; font-weight: 600; }}
            
            a.title-link {{ text-decoration: none; color: #2c3e50; font-size: 1.3em; font-weight: 700; display: block; margin-bottom: 12px; line-height: 1.3; transition: color 0.2s; }}
            a.title-link:hover {{ color: #0061ff; }}
            .summary {{ color: #555; font-size: 0.95em; line-height: 1.6; margin: 0; }}

            /* 空状态提示 */
            .empty-msg {{ text-align: center; padding: 60px 20px; color: #888; }}
            .empty-msg h3 {{ color: #ccc; font-size: 3em; margin: 0 0 20px 0; }}

            /* 页尾 Logo 区域 */
            .footer {{ margin-top: 60px; text-align: center; padding-top: 20px; border-top: 2px solid rgba(0,0,0,0.05); }}
            .tiagile-logo {{
                font-size: 1.8rem;
                font-weight: 800;
                color: #2c3e50;
                letter-spacing: -1px;
                display: inline-block;
                /* 如果你有图片Logo，可以用 img 标签替换掉下面这个 span */
            }}
            .tiagile-logo span {{ color: #0061ff; }} /* 给字母 'i' 加个色 */
            .footer-note {{ color: #aaa; font-size: 0.8em; margin-top: 10px; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header-section">
                <h1>⚡️ UWB & IoT 行业情报站</h1>
                <p class="date">{datetime.now().strftime('%Y.%m.%d')} | Daily Briefing</p>
            </div>
            
            {'<div class="empty-msg"><h3>¯\_(ツ)_/¯</h3><p>过去 7 天内暂未监测到核心信息更新。</p></div>' if not unique_articles else ''}
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
        </div> </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("完成！华丽版页面已生成。")

if __name__ == "__main__":
    generate_newsletter()
