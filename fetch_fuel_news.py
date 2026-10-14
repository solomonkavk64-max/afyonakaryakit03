import os
import re
from datetime import datetime, timezone, timedelta
import feedparser
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SADECE Ulusal ve Prestijli Haber Siteleri (Google News çıkarıldı)
RSS_FEEDS = [
    "https://www.trthaber.com/ekonomi_articles.rss",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.bloomberght.com/rss",
    "https://www.dunya.com/rss?kategori=ekonomi",
    "https://www.hurriyet.com.tr/rss/ekonomi",
    "https://www.milliyet.com.tr/rss/rssnew/ekonomiresimli.xml",
    "https://www.sabah.com.tr/rss/ekonomi.xml",
    "https://www.sozcu.com.tr/kategori/ekonomi/feed",
    "https://www.ensonhaber.com/rss/ekonomi.xml",
    "https://www.enerjigunlugu.net/feed"
]

# BAŞLIKTA OLMAK ZORUNDA OLAN SAF AKARYAKIT KELİMELERİ
MUST_HAVE_IN_TITLE = [
    "akaryakıt", "benzin", "motorin", "mazot", "lpg", "otogaz", "brent petrol", "brent"
]

# YEREL VE ALAKASIZ KELİME ENGELİ
EXCLUDE_KEYWORDS = [
    "kpss", "sınav", "kaçakçılık", "alkol", "tütün", "sigara", "enflasyon", 
    "faiz", "borsa", "hisse", "palamut", "balık", "facebook", "trump", "grönland",
    # Şehir isimleri (Yerel haberleri engellemek için)
    "muğla", "izmir", "ankara", "istanbul", "bursa", "antalya", "adana", "konya", 
    "trabzon", "eskişehir", "ege saati", "yenigün"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def is_strictly_national_fuel_news(title, entry_date):
    title_lower = title.lower()
    
    # 1. Yerel veya alakasız kelime varsa eliyoruz
    if any(ex in title_lower for ex in EXCLUDE_KEYWORDS):
        return False
        
    # 2. SADECE BAŞLIKTA zorunlu akaryakıt kelimelerinden en az biri olmalı
    if not any(kw in title_lower for kw in MUST_HAVE_IN_TITLE):
        return False
        
    # 3. Günlük Tarih Kontrolü (Son 24 saatteki haberler)
    if entry_date:
        now = datetime.now(timezone.utc)
        if entry_date < (now - timedelta(days=1)):
            return False
            
    return True

def fetch_and_store_news():
    print("🧹 Eski haberler temizleniyor...")
    supabase.table("news").delete().neq("id", 0).execute()

    print("🔍 Ulusal basından günlük saf akaryakıt haberleri toplanıyor...")
    news_list = []
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title.strip()
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")

                published_parsed = entry.get("published_parsed", entry.get("updated_parsed"))
                entry_date = None
                if published_parsed:
                    import time
                    entry_date = datetime.fromtimestamp(time.mktime(published_parsed), timezone.utc)

                # Mükerrer başlık kontrolü
                short_title = re.sub(r'[^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]', '', title[:20].lower())
                if short_title in seen_titles:
                    continue

                if is_strictly_national_fuel_news(title, entry_date):
                    seen_titles.add(short_title)
                    news_list.append({
                        "title": title,
                        "content": summary[:250] + "..." if len(summary) > 250 else summary,
                        "url": link
                    })
        except Exception as e:
            print(f"Hata oluşan kaynak ({feed_url}): {e}")

    if news_list:
        supabase.table("news").insert(news_list[:15]).execute()
        print(f"✨ Toplam {len(news_list[:15])} adet ULUSAL VE GÜNLÜK akaryakıt haberi eklendi.")
    else:
        print("Son 24 saatte kriterlere uygun ulusal haber bulunamadı.")

if __name__ == "__main__":
    fetch_and_store_news()
