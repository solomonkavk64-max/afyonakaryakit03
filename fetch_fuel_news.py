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

# Google News Olmayan, Tam 15 Adet Güvenilir Ulusal Ekonomi ve Enerji Kaynağı
RSS_FEEDS = [
    "https://www.enerjigunlugu.net/feed",
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
    "https://www.karar.com/rss/ekonomi",
    "https://www.star.com.tr/rss/rss.asp?kategori=ekonomi",
    "https://www.aksam.com.tr/rss/ekonomi.xml"
]

# BAŞLIKTA OLMAK ZORUNDA OLAN SAF AKARYAKIT KELİMELERİ
MUST_HAVE_IN_TITLE = [
    "akaryakıt", "benzin", "motorin", "mazot", "lpg", "otogaz", "brent petrol", "brent"
]

# YEREL VE ALAKASIZ KELİME / ŞEHİR ENGELİ
EXCLUDE_KEYWORDS = [
    "kpss", "sınav", "kaçakçılık", "alkol", "tütün", "sigara", "enflasyon", 
    "faiz", "borsa", "hisse", "palamut", "balık", "facebook", "trump", "grönland",
    "muğla", "izmir", "ankara", "istanbul", "bursa", "antalya", "adana", "konya", 
    "trabzon", "eskişehir", "ege saati", "yenigün"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def is_valid_fuel_news(title, entry_date):
    title_lower = title.lower()
    
    # 1. Yasaklı/yerel kelimeler varsa eliyoruz
    if any(ex in title_lower for ex in EXCLUDE_KEYWORDS):
        return False
        
    # 2. SADECE BAŞLIKTA zorunlu akaryakıt kelimelerinden biri olmalı
    if not any(kw in title_lower for kw in MUST_HAVE_IN_TITLE):
        return False
        
    # 3. Tarih Kontrolü (Son 48 saat / 2 gün)
    if entry_date:
        now = datetime.now(timezone.utc)
        if entry_date < (now - timedelta(days=2)):
            return False
            
    return True

def fetch_and_store_news():
    print("🧹 Eski haberler temizleniyor...")
    supabase.table("news").delete().neq("id", 0).execute()

    print("🔍 15 ulusal ekonomi ve enerji kaynağından saf akaryakıt haberleri taranıyor...")
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

                if is_valid_fuel_news(title, entry_date):
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
        print(f"✨ Toplam {len(news_list[:15])} adet ulusal akaryakıt haberi eklendi.")
    else:
        print("Kriterlere uygun yeni haber bulunamadı.")

if __name__ == "__main__":
    fetch_and_store_news()
