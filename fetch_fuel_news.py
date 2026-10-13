import os
import feedparser
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

rss_urls = [
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.cnnturk.com/feed/rss/ekonomi/news"
]

# Sadece doğrudan akaryakıt, petrol ve yakıt türleri (Genel ekonomi kelimeleri tamamen silindi)
PURE_FUEL_KEYWORDS = [
    'benzin', 'motorin', 'lpg', 'otogaz', 'akaryakıt', 
    'petrol', 'brent', 'mazot', 'motorine', 'benzine', 'akaryakıta',
    'tüpraş', 'opet', 'shell', 'poş', 'bp', 'opec'
]

def is_pure_fuel_news(title, summary):
    text = f"{title} {summary}".lower()
    # Haberin içinde mutlaka bu saf akaryakıt kelimelerinden en az biri geçmek zorunda
    return any(word in text for word in PURE_FUEL_KEYWORDS)

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
                if is_pure_fuel_news(title, summary):
                    seen_titles.add(title)
                    news_list.append({
                        "title": title,
                        "content": summary,
                        "url": link
                    })
                
    return news_list

def update_news_table():
    print("🧹 Eski ve alakasız haberler temizleniyor...")
    try:
        supabase.table('news').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Eski haberler silinirken hata: {e}")

    print("🔍 Sadece saf akaryakıt ve petrol haberleri taranıyor...")
    fresh_news = fetch_fresh_news()

    if fresh_news:
        print(f"✨ Filtrelenen saf akaryakıt haberi sayısı: {len(fresh_news)}")
        supabase.table('news').insert(fresh_news).execute()
        print("İşlem başarıyla tamamlandı!")
    else:
        print("Kriterlere uyan yeni akaryakıt haberi bulunamadı.")

if __name__ == "__main__":
    update_news_table()
