import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import urllib.parse

# --- 1. 核心关键词配置 ---
TARGET_KEYWORDS = [
    "UWB", "Ultra-Wideband", "Ultra Wideband", "超宽带", 
    "FiRa", "802.15.4z", "CCC Digital Key", 
    "NXP", "Qorvo", "STMicroelectronics", "Apple U1", 
    "纽瑞芯", "NewRadio", "驰芯", "Cixin", "加特兰", "Calterah",
    "精位科技", "全迹科技", "TSingo", "信维通信", "浩云科技"
]

# --- 2. 构造搜索源 ---
def get_google_rss_url(query):
    encoded_query = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

RSS_FEEDS = [
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.macrumors.com/macrumors.xml",
    "https://www.iot-now.com/feed/",
    "https://9to5mac.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    get_google_rss_url("UWB 芯片"),
    get_google_rss_url("UWB 产业"),
    get_google_rss_url("AirTag"),
    get_google_rss_url("Apple UWB"),
    get_google_rss_url("超宽带技术"),
    get_google_rss_url("纽瑞芯 OR 驰芯 OR 加特兰 OR 恩智浦 UWB"),
]

# --- 3. 辅助工具 ---
def clean_summary(html_text, source_name=""):
    if not html_text: return ""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 清洗 Google News 尾巴
        text = text.replace("Google 新闻的完整报道", "").replace("See full coverage on Google News", "")
        
        # 切掉来源名称
        if source_name and len(source_name) > 1:
            text = re.sub(re.escape(source_name), '', text, flags=re.IGNORECASE).strip()
            text = text.rstrip(" -|:：")

        return text
    except:
        return html_text[:100]

def is_recent(entry_date_parsed):
    if not entry_date_parsed: return True 
    try:
        news_date = datetime.fromtimestamp(time.mktime(entry_date_parsed))
        return (datetime.now() - news_date).days <= 30
    except:
        return True 

def check_keywords(text):
    text = text.lower()
    for kw in TARGET_KEYWORDS:
        if kw.lower() in text:
            return True
    return False

# --- 4. 智能分类逻辑 ---
def get_category(title, summary):
    text = (title + summary).lower()
    if any(k in text for k in ["fira", "802.15.4z", "ccc", "alliance", "联盟", "标准", "协议"]):
        return "standards"
    
    chip_keywords = [
        "nxp", "qorvo", "apple", "stmicro", "纽瑞芯", "驰芯", 
        "加特兰", "芯片", "ic", "半导体", "发布"
    ]
    if any(k in text for k in chip_keywords):
        return "chips"
        
    return "general"

# 针对 FiRa 官网
def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    return [{
        'title': "FiRa 联盟官方新闻中心 (点击直达)",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now().timetuple(),
        'summary': "FiRa 联盟官方发布的最新标准、认证产品及成员动态。",
        'category': 'standards'
    }]

# --- 5. 核心逻辑 ---
def fetch_feed(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' 
        if response.status_code != 200: return None
        return feedparser.parse(response.content)
    except: return None

def generate_newsletter():
    articles = []
    print("🚀 开始全网抓取...")
    
    # 1. 抓取
    for url in RSS_FEEDS:
        feed = fetch_feed(url)
        if not feed or not feed.entries: continue
            
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed') and not is_recent(entry.published_parsed):
                continue
            
            summary_raw = entry.get('summary', entry.get('description', ''))
            content_to_check = f"{entry.title} {summary_raw}"
            
            if check_keywords(content_to_check):
                source_name = feed.feed.get('title', 'Network Source')
                title_clean = entry.title
                real_source_name_for_cleaning = "" 

                if "Google" in source_name:
                    source_name = "Google News"
                
                if " - " in title_clean:
                    parts = title_clean.rsplit(" - ", 1)
                    title_clean = parts[0]
                    real_source = parts[1]
                    source_name = f"{real_source}"
                    real_source_name_for_cleaning = real_source 

                # 清洗摘要
                final_summary = clean_summary(summary_raw, real_source_name_for_cleaning)

                # 🔥 智能隐藏逻辑 🔥
                # 去除标点和空格进行核心内容比对
                t_core = re.sub(r'[^\w]', '', title_clean)
                s_core = re.sub(r'[^\w]', '', final_summary)
                
                # 如果摘要被包含在标题里，或者标题包含在摘要里，判定为重复
                if len(s_core) > 0 and (s_core in t_core or t_core in s_core):
                    # 如果长度差异很小（说明没有额外信息），把摘要设为空
                    if abs(len(s_core) - len(t_core)) < 20:
                        final_summary = "" # 彻底清空，不显示
                
                # 如果摘要本身就太短，也隐藏
                if len(final_summary) < 5:
                    final_summary = ""

                # 截断过长摘要
                if len(final_summary) > 120: 
                    final_summary = final_summary[:120] + "..."

                category = get_category(title_clean, summary_raw)

                articles.append({
                    'title': title_clean,
                    'link': entry.link,
                    'source': source_name,
                    'date': entry.get('published_parsed', datetime.now().timetuple()),
                    'summary': final_summary, # 这里可能是空字符串
                    'category': category
                })

    # 2. 加入 FiRa 并去重
    articles.extend(scrape_fira_news())
    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
    
    unique_articles.sort(key=lambda x: time.mktime(x['date']) if x['date'] else 0, reverse=True)

    # 3. 分组
    modules = {
        "standards": [],
        "chips": [],
        "general": []
    }
    for art in unique_articles:
        modules[art['category']].append(art)

    # 4. 生成 HTML
    cat_titles = {
        "standards": "🏛️ 权威发布 & 标准动态",
        "chips": "💎 芯片原厂 & 核心技术",
        "general": "📰 行业应用 & 市场资讯"
    }

    content_html = ""
    for cat_key, arts in modules.items():
        if not arts: continue 
        
        section_html = f"""
        <div class="section-header">{cat_titles[cat_key]}</div>
        <div class="news-grid">
        """
        
        for art in arts:
            try: date_str = time.strftime('%m-%d', art['date'])
            except: date_str = "Recent"
            
            # 🔥 HTML 生成时的判断逻辑 🔥
            # 只有当 summary 不为空时，才生成 <p> 标签
            summary_html = ""
            if art['summary']:
                summary_html = f'<p class="summary">{art["summary"]}</p>'
            
            section_html += f"""
            <div class="card">
                <div class="meta-info">
                    <span class="tag">{cat_key.upper()}</span>
                    <span class="source">{art['source']} · {date_str}</span>
                </div>
                <a href="{art['link']}" class="title-link" target="_blank">{art['title']}</a>
                {summary_html}
            </div>
            """
        section_html += "</div>"
        content_html += section_html

    if not unique_articles:
        content_html = '<div class="empty-msg"><h3>📡</h3><p>正在扫描全网数据...</p></div>'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tiagile - UWB & IoT 行业情报</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Noto+Sans+SC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary-color: #0061ff; --bg-color: #f4f7fa; }}
            body {{
                font-family: 'Poppins', 'Noto Sans SC', sans-serif;
                margin: 0; padding: 0;
                background-color: var(--bg-color);
                background-image: linear-gradient(rgba(244, 247, 250, 0.9), rgba(244, 247, 250, 0.9)), url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80');
                background-size: cover; background-attachment: fixed;
                color: #333;
            }}
            .main-container {{
                max-width: 1000px;
                margin: 40px auto; padding: 20px;
            }}
            .header-section {{ text-align: center; margin-bottom: 40px; padding: 20px; }}
            h1 {{
                font-weight: 800; font-size: 2.5rem; margin: 0;
                background: linear-gradient(135deg, #0061ff, #60efff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                letter-spacing: -1px;
            }}
            .date {{ color: #666; font-weight: 600; margin-top: 5px; font-size: 0.9rem; text-transform: uppercase; }}

            .section-header {{
                font-size: 1.4rem; font-weight: 700; color: #2c3e50;
                margin: 30px 0 15px 0; padding-left: 15px;
                border-left: 5px solid var(--primary-color);
            }}
            
            .news-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 20px;
            }}

            .card {{
                background: #ffffff; padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.03);
                transition: transform 0.2s, box-shadow 0.2s;
                border: 1px solid rgba(0,0,0,0.05);
                display: flex; flex-direction: column;
            }}
            .card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); }}
            
            .meta-info {{ display: flex; align-items: center; margin-bottom: 10px; font-size: 0.8em; }}
            .tag {{ 
                background: #eef4ff; color: var(--primary-color); 
                padding: 3px 8px; border-radius: 6px; font-weight: 700; margin-right: 8px; 
            }}
            .source {{ color: #888; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            
            a.title-link {{ 
                text-decoration: none; color: #1a1a1a; font-size: 1.1rem; font-weight: 700; 
                line-height: 1.4; margin-bottom: 5px; /* 减小下边距，因为可能没有摘要 */
                display: block;
            }}
            a.title-link:hover {{ color: var(--primary-color); }}
            
            .summary {{ 
                color: #555; font-size: 0.9rem; line-height: 1.6; 
                margin: 5px 0 0 0; /* 调整间距 */
                flex-grow: 1; 
            }}

            .footer {{ margin-top: 60px; text-align: center; color: #aaa; font-size: 0.8rem; padding-bottom: 20px; }}
            .tiagile-logo {{ font-size: 1.5rem; font-weight: 800; color: #2c3e50; }}
            .tiagile-logo span {{ color: #0061ff; }}

            @media (max-width: 600px) {{
                .news-grid {{ grid-template-columns: 1fr; }}
                h1 {{ font-size: 2rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header-section">
                <h1>⚡️ UWB & IoT 行业情报站</h1>
                <p class="date">{datetime.now().strftime('%Y.%m.%d')} | Tiagile Daily Briefing</p>
            </div>
            
            {content_html}

            <div class="footer">
                <div class="tiagile-logo">T<span>i</span>agile</div>
                <p>Intelligence Powered by GitHub Actions</p>
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

