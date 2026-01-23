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
    "https://www.iot-now.com/feed/",
    get_google_rss_url("UWB 芯片"),
    get_google_rss_url("UWB 产业"),
    get_google_rss_url("超宽带技术"),
    get_google_rss_url("纽瑞芯 OR 长沙驰芯 OR 加特兰 OR 恩智浦 UWB"),
]

# --- 3. 辅助工具：更强的清洗逻辑 ---
def clean_summary(html_text, source_name=""):
    if not html_text: return "暂无详细摘要，请点击标题阅读原文。"
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 1. 清洗 Google News 尾巴
        text = text.replace("Google 新闻的完整报道", "").replace("See full coverage on Google News", "")
        
        # 2. ✂️ 手术刀：如果来源名字出现在摘要里，把它切掉
        # 比如来源是 "Sohu"，摘要结尾是 "... Sohu"，则删除
        if source_name and len(source_name) > 1:
            # 去除来源名称（忽略大小写）
            text = re.sub(re.escape(source_name), '', text, flags=re.IGNORECASE).strip()
            # 去除来源名称可能带来的多余标点
            text = text.rstrip(" -|:：")

        if len(text) < 5: return "点击标题查看详情..."
        if len(text) > 120: return text[:120] + "..."
        return text
    except:
        return html_text[:100] + "..."

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
    # 优先级 1: 联盟与标准
    if any(k in text for k in ["fira", "802.15.4z", "ccc", "alliance", "联盟", "标准", "协议"]):
        return "standards"
    # 优先级 2: 芯片与大厂
    if any(k in text for k in ["nxp", "q
