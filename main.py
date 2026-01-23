import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import urllib.parse

# --- 1. 定义核心监测目标 ---
TARGET_KEYWORDS = [
    "UWB", "Ultra-Wideband", "Ultra Wideband", "超宽带", 
    "FiRa", "802.15.4z", "CCC Digital Key", 
    "NXP", "Qorvo", "STMicroelectronics", "Apple U1", 
    "纽瑞芯", "NewRadio", "驰芯", "Cixin", "加特兰", "Calterah",
    "精位科技", "全迹科技", "TSingo", "信维通信", "浩云科技"
]

# --- 2. 构造更强的 Bing 搜索源 ---
def get_bing_rss_url(query):
    # 强制加上 sortBy=Date，虽然 Bing 不一定百分百听话，但能增加获取新内容的概率
    encoded_query = urllib.parse.quote(query)
    return f"https://www.bing.com/news/search?q={encoded_query}&format=rss&sortBy=Date"

RSS_FEEDS = [
    # --- A. 国际源 (英文 - 保持稳定) ---
    "https://techcrunch.com/tag/ultra-wideband/feed/",
    "https://www.iotforall.com/feed",
    "https://www.iot-now.com/feed/",
    
    # --- B. 中文广域搜索 (不再局限于 mp.weixin.qq.com) ---
    # 策略：多用几个行业词，把腾讯网、搜狐等收录的公众号文章都炸出来
    get_bing_rss_url("UWB 芯片"),
    get_bing_rss_url("UWB 产业"),
    get_bing_rss_url("UWB 定位"),
    get_bing_rss_url("超宽带 技术"),
    
    # --- C. 重点厂商定向轰炸 ---
    get_bing_rss_url("纽瑞芯 OR 长沙驰芯 OR 加特兰 OR 恩智浦 UWB"),
]

# --- 3. 辅助工具 (放宽限制) ---
def clean_summary(html_text):
    if not html_text: return "暂无详细摘要，请点击标题阅读原文。"
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace("See full coverage on Google News", "")
        if len(text) < 5: return "点击标题查看详情..."
        if len(text) > 140: return text[:140] + "..."
        return text
    except:
        return html_text[:100] + "..."

def is_recent(entry_date_parsed):
    if not entry_date_parsed: return True # 如果没抓到时间，默认放行！先看到数据再说
    try:
        news_date = datetime.fromtimestamp(time.mktime(entry_date_parsed))
        # ⚠️ 关键修改：放宽到 30 天，确保能抓到中文内容
        return (datetime.now() - news_date).days <= 30
    except:
        return True 

def check_keywords(text):
    text = text.lower()
    for kw in TARGET_KEYWORDS:
        if kw.lower() in text:
            return True
    return False

# 针对 FiRa 官网
def scrape_fira_news():
    url = "https://www.firaconsortium.org/about/news-events/press-releases"
    return [{
        'title': "🔗 FiRa 联盟官方新闻中心 (点击直达)",
        'link': url,
        'source': 'FiRa Consortium',
        'date': datetime.now().timetuple(),
        'summary': "FiRa 联盟官方发布的最新标准、认证产品及成员动态。"
    }]

# --- 核心生成逻辑 ---
def generate_newsletter():
    articles = []
    print("🚀 开始全网抓取 UWB 情报 (宽域模式)...")
    
    for url in RSS_FEEDS:
        try:
            print(f"正在扫描: {url} ...")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"  ⚠️ 此源返回了 0 条数据，可能是关键词太偏或 Bing 暂时屏蔽。")
            
            for entry in feed.entries:
                
                # 宽松的时间过滤
                if hasattr(entry, 'published_parsed'):
                    if not is_recent(entry.published_parsed):
                        continue
                
                summary_raw = entry.get('summary', entry.get('description', ''))
                content_to_check = f"{entry.title} {summary_raw}"
                
                if check_keywords(content_to_check):
                    # 来源清洗
                    source_name = feed.feed.get('title', 'Network Source')
                    title_clean = entry.title
                    
                    # 智能标记微信相关内容
                    # 虽然我们不只搜微信域名，但如果来源里有 QQ、Sohu 等，大概率是公众号转载
                    if "qq.com" in entry.link or "tencent" in source_name.lower():
                        source_name = "腾讯网 / 微信生态"
                        title_clean = title_clean.split(" - 腾讯")[0]
                    elif "Bing" in source_name:
                        source_name = "全网聚合 / Bing"
                    
                    articles.append({
                        'title': title_clean,
                        'link': entry.link,
                        'source': source_name,
                        'date': entry.get('published_parsed', datetime.now().timetuple()),
                        'summary': clean_summary(summary_raw)
                    })
        except Exception as e:
            print(f"❌ 源出错: {e}")

    # 加入 FiRa
    articles.extend(scrape_fira_news())

    # 去重
    seen_links = set()
    unique_articles = []
    for art in articles:
        if art['link'] not in seen_links:
            unique_articles.append(art)
            seen_links.add(art['link'])
            
    # 排序
    unique_articles.sort(key=lambda x: time.mktime(x['date']) if x['date'] else 0, reverse=True)

    # 空状态
    empty_html = ""
    if len(unique_articles) <= 1:
        empty_html = '<div class="empty-msg"><h3>📡</h3><p>正在扫描全网数据，暂未发现 30 天内的核心关键词匹配项。</p></div>'

    # 生成 HTML (UI 保持不变)
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
                font-family: 'Poppins', 'Noto Sans SC', sans-serif;
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
