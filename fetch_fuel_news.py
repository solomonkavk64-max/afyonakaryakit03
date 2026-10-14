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

# Genişletilmiş Haber Kaynakları
RSS_FEEDS = [
    "https://www.trthaber.com/ekonomi_articles.rss",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "https://www.ensonhaber.com/rss/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.bloomberght.com/rss",
    "https://www.dunya.com/rss?kategori=ekonomi"
]

# Kabul Edilen Akaryakıt ve Enerji Kelimeleri
FUEL_KEYWORDS = [
    "akaryakıt", "benzin", "motorin", "mazot", "lpg", "otogaz", 
    "brent", "petrol", "epdk", "zam", "indirim", "pompa", "tabela fiyat"
]

# Kesinlikle İstenmeyen Alakasız Kelimeler
EXCLUDE_KEYWORDS = [
    "palamut", "balık", "facebook", "faiz", "mevduat", "borsa", 
    "hisse", "kredi", "konut", "ev fiyat", "altın", "gram altın"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def is_valid_news(title, summary, entry_date):
    text = f"{title} {summary}".lower()
    
    # 1. Yasaklı kelime kontrolü
    if any(ex in text for ex in EXCLUDE_KEYWORDS):
        return False
        
    # 2. Akaryakıt/Enerji kelimesi geçiyor mu?
    if not any(kw in text for kw in FUEL_KEYWORDS):
        return False
        
    # 3. Tarih Kontrolü (Eğer RSS'te tarih varsa, son 5 günden eski olmasın)
    if entry_date:
        now = datetime.now(timezone.utc)
        # 5 günden eski haberleri direkt eliyoruz
        if entry_date < (now - timedelta(days=5)):
            return False
            
    return True

def fetch_and_store_news():
    print("🧹 Eski haberler temizleniyor...")
    supabase.table("news").delete().neq("id", 0).execute()

    print("🔍 Taze ve filtrelenmiş akaryakıt haberleri taranıyor...")
    news_list = []
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title.strip()
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")

                # Tarihi al (yoksa güncel kabul et)
                published_parsed = entry.get("published_parsed", entry.get("updated_parsed"))
                entry_date = None
                if published_parsed:
                    import time
                    entry_date = datetime.fromtimestamp(time.mktime(published_parsed), timezone.utc)

                # Mükerrer kontrolü
                short_title = re.sub(r'[^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]', '', title[:20].lower())
                if short_title in seen_titles:
                    continue

                if is_valid_news(title, summary, entry_date):
                    seen_titles.add(short_title)
                    news_list.append({
                        "title": title,
                        "content": summary[:250] + "..." if len(summary) > 250 else summary,
                        "url": link
                    })
        except Exception as e:
            print(f"Hata oluşan kaynak ({feed_url}): {e}")

    if news_list:
        # En güncel 15 haberi veritabanına kaydedelim
        supabase.table("news").insert(news_list[:15]).execute()
        print(f"✨ Toplam {len(news_list[:15])} adet taze akaryakıt haberi eklendi.")
    else:
        print("Kriterlere uygun yeni haber bulunamadı.")

if __name__ == "__main__":
    fetch_and_store_news()
