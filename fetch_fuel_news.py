import os
import feedparser
from datetime import datetime, timezone, timedelta
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Çeşitlendirilmiş ve Sektörel RSS Kaynakları
rss_urls = [
    # Çeşitli Genel Ekonomi Akışları
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.cnnturk.com/feed/rss/ekonomi/news",
    "https://www.dünya.com/rss",
    "https://www.bloomberght.com/rss",
    # Otomotiv ve Sektör Portalları
    "https://www.log.com.tr/feed/",
    "https://www.donanimhaber.com/rss/otomobil/"
]

# Sadece doğrudan akaryakıt ve petrol odaklı terimler
PURE_FUEL_KEYWORDS = [
    'benzin', 'motorin', 'lpg', 'otogaz', 'akaryakıt', 
    'petrol', 'brent', 'mazot', 'motorine', 'benzine', 'akaryakıta',
    'tüpraş', 'opet', 'shell', 'opec', 'epdk', 'otogaza'
]

# Akaryakıt dışı ekonomi konularını KESİNLİKLE engelleyen negatif filtre
EXCLUDE_KEYWORDS = [
    'altın', 'gram altın', 'çeyrek', 'dolar', 'euro', 'faiz', 
    'borsa', 'enflasyon', 'konut', 'kredi', 'asgari ücret', 'emekli',
    'mevduat', 'hisse', 'tahvil', 'bitcoin', 'kripto'
]

def is_valid_fuel_news(title, summary):
    text = f"{title} {summary}".lower()
    
    # 1. Alakasız konu tespit edilirse pas geç
    if any(ex in text for ex in EXCLUDE_KEYWORDS):
        return False
        
    # 2. Saf akaryakıt kelimelerinden en az biri bulunmalı
    return any(word in text for word in PURE_FUEL_KEYWORDS)

def fetch_fresh_news():
    news_list = []
    seen_titles = set()
    now = datetime.now(timezone.utc)
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get('title', '').strip()
                summary = entry.get('summary', entry.get('description', '')).strip()
                link = entry.get('link', '').strip()
                
                # Tarih Kontrolü: 48 saatten eski veya tarihi okunamayan haberleri ele
                published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                if not published_parsed:
                    continue
                    
                pub_date = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if now - pub_date > timedelta(hours=48):
                    continue
                
                if title and link and title not in seen_titles:
                    if is_valid_fuel_news(title, summary):
                        seen_titles.add(title)
                        news_list.append({
                            "title": title,
                            "content": summary,
                            "url": link
                        })
        except Exception as e:
            print(f"Kaynak taranırken hata ({url}): {e}")
                
    return news_list

def update_news_table():
    print("🧹 Eski haberler temizleniyor...")
    try:
        supabase.table('news').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Eski haberler silinirken hata: {e}")

    print("🔍 Çeşitlendirilmiş kaynaklardan sadece taze akaryakıt haberleri çekiliyor...")
    fresh_news = fetch_fresh_news()

    if fresh_news:
        print(f"✨ Toplam {len(fresh_news)} adet güncel akaryakıt haberi eklendi.")
        supabase.table('news').insert(fresh_news).execute()
        print("İşlem başarıyla tamamlandı!")
    else:
        print("Son 48 saat içinde kriterlere uyan akaryakıt haberi bulunamadı.")

if __name__ == "__main__":
    update_news_table()
