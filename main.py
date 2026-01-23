import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import urllib.parse

# --- 1. 定义核心监测目标 (中英文) ---
# 只要新闻包含这些词，就会被抓取
TARGET_KEYWORDS = [
    "UWB", "Ultra-Wideband", "Ultra Wideband", "超宽带", # 核心技术词
    "FiRa", "802.15.4z", "CCC Digital Key", # 标准词
    "NXP", "Qorvo", "STMicroelectronics", "Apple U1", # 国际大厂
    "纽瑞芯", "NewRadio", # 重点国产厂商
    "驰芯", "Cixin", 
    "加特兰", "Calterah", # 虽然主做雷达，但也监控
    "精位科技", "全迹科技" # 其他潜在相关
]

# --- 2. 构造智能新闻源 ---
# 我们利用 Bing News 的 RSS 接口来帮我们搜索全网
def get_bing_rss_url(query):
    encoded_query = urllib.parse.quote(query)
    return f"https://www.bing.com/news/search?q={encoded_query}&format=rss"

RSS_FEEDS = [
    # --- 国际源 ---
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    
    # --- 中文智能聚合源 (代替手动爬官网) ---
    # 搜索：UWB 行业新闻
    get_bing_rss_url("UWB 超宽带"),
    # 搜索：特定厂商动态 (用 OR 连接)
    get_bing_rss_url("纽瑞芯 OR 长沙驰芯 OR 加特兰 OR 恩智浦 UWB"),
]

# --- 3. 辅助工具 (保持稳定) ---
def clean_summary(html_text):
    if not html_text: return "暂无详细摘要，请点击标题阅读原文。"
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        # 移除一些常见的新闻源噪音
        text = text.replace("See full coverage on Google News", "")
        if len(text) < 5: return "点击标题查看详情..."
        if len(text) > 140: return text[:140] + "..."
        return text
    except:
        return html_text[:100] + "..."

def is_recent(entry_date_parsed):
    if not entry_date_parsed: return False # 如果没有时间，为了保险起见，这行可以根据需要调整
    try:
        news_date = datetime.fromtimestamp(time.mktime(entry_date_parsed))
        # 放宽一点时间限制，监测最近 14 天的动态，以免漏掉重要厂商的低频更新
        return (datetime.now() - news_date).days <= 14
    except:
        return True # 如果解析时间失败，默认保留，以免漏掉

def check_keywords(text):
    text = text.lower()
    for kw in TARGET_KEYWORDS:
        if kw.lower() in text:
            return True
    return False

# --- 4. 专门针对 FiRa 官网的抓取 (因为它是静态网页) ---
def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    # 这里只是一个占位符，实际生产环境建议依赖 Bing News 抓取 FiRa 的 PR
    # 为了演示，我们保留这个功能，作为一个固定入口
    return [{
        'title': "🔗 FiRa 联盟官方新闻中心 (点击直达)",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now().timetuple(),
        'summary': "FiRa 联盟官方发布的最新标准、认证产品及成员动态。"
    }]

# --- 5. 核心逻辑 ---
def generate_newsletter():
    articles = []
    print("🚀 开始全网抓取 UWB 情报...")
    
    for url in RSS_FEEDS:
        try:
            print(f"正在扫描: {url} ...")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                
                # 1. 时间过滤
                if hasattr(entry, 'published_parsed'):
                    if not is_recent(entry.published_parsed):
                        continue
                
                # 2. 关键词匹配
                # 组合标题和摘要进行检查
                summary_raw = entry.get('summary', entry.get('description', ''))
                content_to_check = f"{entry.title} {summary_raw}"
                
                if check_keywords(content_to_check):
                    # 确定来源名称
                    source_name = feed.feed.get('title', 'Network Source')
                    if "Bing" in source_name:
                        source_name = "全网聚合 / Bing"
                    
                    articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'source': source_name,
                        'date': entry.get('published_parsed', datetime.now().timetuple()),
                        'summary': clean_summary(summary_raw)
                    })
        except Exception as e:
            print(f"❌ 源出错: {e}")

    # 加入 FiRa 固定入口
    articles.extend(scrape_fira_news())

    # 去重 (根据链接)
    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
            
    # 按时间排序
    unique_articles.sort(key=lambda x: time.mktime(x['date']) if x['date'] else 0, reverse=True)

    # 准备空状态 HTML
    empty_html = ""
    if len(unique_articles) <= 1: # 只有FiRa一条时
        empty_html = '<div class="empty-msg"><h3>📡</h3><p>正在扫描全网数据，今日暂无特定重大更新。</p></div>'

    # 生成 HTML (保持你喜欢的华丽 UI)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tiagile - UWB & IoT 行业情报</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Poppins', 'Noto Sans SC', sans-serif; /* 增加了中文字体支持 */
                margin: 0; padding: 0;
                background: linear-gradient(rgba(240, 242, 250, 0.9), rgba(240, 242, 250, 0.9)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
                background-size: cover; background-attachment: fixed; background-position: center;
                min-height: 100vh; display: flex; justify-content: center; align-items: flex-start;
            }}
            .main-container {{
                width: 90%; max-width: 800px; margin: 60px 0; padding: 40px;
                background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.6);
            }}
            .header-section {{ text-align: center; margin-bottom: 50px; }}
            h1 {{
                font-weight: 800; font-size: 2.4rem; margin-bottom: 10px;
                background: linear-gradient(135deg, #0061ff, #60efff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                display: inline-block; letter-spacing: -1px;
            }}
            .date {{ color: #555; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; font-size: 0.9rem; }}
            
            .card {{
                background: #ffffff; padding: 25px; margin-bottom: 25px;
                border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); transition: all 0.3s ease;
                border-left: 6px solid #0061ff; position: relative;
            }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }}
            
            .meta-info {{ display: flex; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
            .tag {{ 
                background: linear-gradient(135deg, #0061ff, #60efff); color: white; 
                padding: 4px 12px; border-radius: 20px; font-size: 0.7em; font-weight: 700; 
                margin-right: 10px; box-shadow: 0 2px 5px rgba(0,97,255,0.3);
            }}
            .source {{ color: #888; font-size: 0.85em; font-weight: 600; }}
            
            a.title-link {{ 
                text-decoration: none; color: #1a1a1a; font-size: 1.25em; font-weight: 700; 
                display: block; margin-bottom: 12px; line-height: 1.4; transition: color 0.2s;
            }}
            a.title-link:hover {{ color: #0061ff; }}
            .summary {{ color: #555; font-size: 0.95em; line-height: 1.7; margin: 0; text-align: justify; }}
            
            .empty-msg {{ text-align: center; padding: 60px 20px; color: #888; }}
            .empty-msg h3 {{ font-size: 3em; margin: 0 0 20px 0; }}
            
            .footer {{ margin-top: 60px; text-align: center; padding-top: 30px; border-top: 2px solid rgba(0,0,0,0.05); }}
            .tiagile-logo {{ font-size: 1.8rem; font-weight: 800; color: #2c3e50; letter-spacing: -1px; display: inline-block; }}
            .tiagile-logo span {{ color: #0061ff; }}
            .footer-note {{ color: #aaa; font-size: 0.8em; margin-top: 10px; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header-section">
                <h1>⚡️ UWB & IoT 行业情报站</h1>
                <p class="date">{datetime.now().strftime('%Y.%m.%d')} | Tiagile Daily Briefing</p>
            </div>
            
            {empty_html}
    """
    
    for art in unique_articles:
        # 日期处理
        try:
            date_str = time.strftime('%m-%d', art['date'])
        except:
            date_str = "Recent"
            
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
    print("完成！index.html 已生成。")

if __name__ == "__main__":
    generate_newsletter()
