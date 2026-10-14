import os
import re
import feedparser
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Odaklanmış RSS Kaynakları
RSS_FEEDS = [
    "https://www.trthaber.com/ekonomi_articles.rss",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "https://www.ensonhaber.com/rss/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.bloomberght.com/rss",
    "https://www.dunya.com/rss?kategori=ekonomi"
]

# ZORUNLU AKARYAKIT KELİMELERİ (Haberde bunlardan en az BİRİ olmak ZORUNDA)
PURE_FUEL_KEYWORDS = [
    "akaryakıt", "benzin", "motorin", "mazot", "lpg", "otogaz", 
    "brent petrol", "epdk", "pompa fiyat", "yakıt"
]

# YASAKLI KELİMELER (Bunlar geçerse haber DİREKT ELENİR)
EXCLUDE_KEYWORDS = [
    "palamut", "balık", "facebook", "faiz", "mevduat", "borsa", 
    "hisse", "kredi", "ev fiyat", "konut", "kuruş", "dolar", "euro"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def is_pure_fuel_news(title, summary):
    text = f"{title} {summary}".lower()
    
    # 1. Yasaklı kelime varsa eliyoruz
    if any(ex in text for ex in EXCLUDE_KEYWORDS):
        return False
        
    # 2. Zorunlu akaryakıt kelimelerinden en az biri olmalı
    return any(keyword in text for keyword in PURE_FUEL_KEYWORDS)

def fetch_and_store_news():
    print("🧹 Eski haberler temizleniyor...")
    supabase.table("news").delete().neq("id", 0).execute()

    print("🔍 Saf akaryakıt haberleri taranıyor...")
    news_list = []
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title.strip()
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")

                # Mükerrer Kontrolü (Başlığın ilk 20 harfi bazında benzeşme tespiti)
                short_title = re.sub(r'[^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]', '', title[:20].lower())
                if short_title in seen_titles:
                    continue

                if is_pure_fuel_news(title, summary):
                    seen_titles.add(short_title)
                    news_list.append({
                        "title": title,
                        "content": summary[:250] + "..." if len(summary) > 250 else summary,
                        "url": link
                    })
        except Exception as e:
            print(f"Hata oluşan kaynak ({feed_url}): {e}")

    if news_list:
        supabase.table("news").insert(news_list[:10]).execute()
        print(f"✨ Toplam {len(news_list[:10])} adet GERÇEK akaryakıt haberi eklendi.")
    else:
        print("Kriterlere uygun yeni akaryakıt haberi bulunamadı.")

if __name__ == "__main__":
    fetch_and_store_news()
