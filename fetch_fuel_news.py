import os
import feedparser
from datetime import datetime, timezone, timedelta
from supabase import create_client

# GitHub Secrets üzerinden Supabase bağlantı bilgileri
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Takip edilen RSS kaynakları
rss_urls = [
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss"
]

# Sadece doğrudan akaryakıt ve petrol ile ilgili net kelimeler (Genel kelimeler temizlendi)
STRICT_KEYWORDS = [
    'benzin', 'motorin', 'lpg', 'otogaz', 'akaryakıt', 
    'petrol', 'brent', 'mazot', 'motorine', 'benzine', 'akaryakıta'
]

def is_strictly_fuel_related(title, summary):
    text = f"{title} {summary}".lower()
    return any(word in text for word in STRICT_KEYWORDS)

def fetch_fresh_news():
    news_list = []
    seen_titles = set()
    now = datetime.now(timezone.utc)
    
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()
            link = entry.get('link', '').strip()
            
            # Tarih kontrolü: 48 saatten (2 günden) eski haberleri kesinlikle ele
            published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
            if published_parsed:
                pub_date = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if now - pub_date > timedelta(hours=48):
                    continue

            # Başlık ve bağlantı varsa ve doğrudan akaryakıt kelimesi içeriyorsa ekle
            if title and link and title not in seen_titles:
                if is_strictly_fuel_related(title, summary):
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

    print("🔍 Sadece bugüne ait taze akaryakıt haberleri taranıyor...")
    fresh_news = fetch_fresh_news()

    if fresh_news:
        print(f"✨ Eklenen güncel akaryakıt haberi sayısı: {len(fresh_news)}")
        supabase.table('news').insert(fresh_news).execute()
        print("İşlem başarıyla tamamlandı!")
    else:
        print("Bugüne ait kriterlere uyan yeni akaryakıt haberi bulunamadı.")

if __name__ == "__main__":
    update_news_table()
