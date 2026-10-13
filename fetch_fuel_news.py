import os
import feedparser
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Daha zengin haber kaynağı
rss_urls = [
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.cnnturk.com/feed/rss/ekonomi/news"
]

KEYWORDS = [
    'benzin', 'motorin', 'lpg', 'otogaz', 'akaryakıt', 
    'petrol', 'brent', 'mazot', 'motorine', 'benzine', 'akaryakıta',
    'epdk', 'opec', 'enerji', 'zam', 'indirim', 'fiyat'
]

def is_fuel_related(title, summary):
    text = f"{title} {summary}".lower()
    return any(word in text for word in KEYWORDS)

def fetch_fresh_news():
    news_list = []
    seen_titles = set()
    
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()
            link = entry.get('link', '').strip()
            
            if title and link and title not in seen_titles:
                if is_fuel_related(title, summary):
                    seen_titles.add(title)
                    news_list.append({
                        "title": title,
                        "content": summary,
                        "url": link
                    })
                
    return news_list

def update_news_table():
    print("🧹 Eski haberler temizleniyor...")
    try:
        supabase.table('news').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Eski haberler silinirken hata oluştu: {e}")

    print("🔍 Güncel haberler taranıyor...")
    fresh_news = fetch_fresh_news()

    if fresh_news:
        print(f"✨ Eklenen toplam haber sayısı: {len(fresh_news)}")
        supabase.table('news').insert(fresh_news).execute()
        print("İşlem başarıyla tamamlandı!")
    else:
        print("Kriterlere uyan yeni haber bulunamadı.")

if __name__ == "__main__":
    update_news_table()
