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

# Genişletilmiş Haber Kaynakları (TRT, AA, Ensonhaber, NTV, Habertürk, Dünya vb.)
RSS_FEEDS = [
    "https://www.trthaber.com/ekonomi_articles.rss",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "https://www.ensonhaber.com/rss/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.bloomberght.com/rss",
    "https://www.dunya.com/rss?kategori=ekonomi"
]

# Duyuru sekmesi için Akaryakıt Filtre Kelimeleri
FUEL_KEYWORDS = [
    "akaryakıt", "benzin", "motorin", "mazot", "lpg", "otogaz", 
    "epdk", "brent petrol", "petrol fiyat", "zam", "indirim", "pompa fiyat"
]

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def is_fuel_news(title, summary):
    text = f"{title} {summary}".lower()
    return any(keyword in text for keyword in FUEL_KEYWORDS)

def fetch_and_store_news():
    print("🧹 Eski haberler temizleniyor...")
    # id sütunu bigint olduğu için sayısal 0 kontrolü yapıyoruz:
    supabase.table("news").delete().neq("id", 0).execute()

    print("🔍 TRT, AA ve diğer geniş kaynaklardan akaryakıt haberleri çekiliyor...")
    news_list = []
    seen_titles = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title.strip()
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")

                if title in seen_titles:
                    continue

                if is_fuel_news(title, summary):
                    seen_titles.add(title)
                    news_list.append({
                        "title": title,
                        "content": summary[:250] + "..." if len(summary) > 250 else summary,
                        "url": link
                    })
        except Exception as e:
            print(f"Hata oluşan kaynak ({feed_url}): {e}")

    if news_list:
        # En güncel 15 haberi alıp veritabanına ekleyelim
        supabase.table("news").insert(news_list[:15]).execute()
        print(f"✨ Toplam {len(news_list[:15])} adet güncel akaryakıt haberi eklendi.")
    else:
        print("Gerekli kriterlere uygun yeni haber bulunamadı.")

if __name__ == "__main__":
    fetch_and_store_news()
