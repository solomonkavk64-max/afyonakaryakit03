import feedparser
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Çalışan alternatifi yüksek RSS Kaynakları (Habertürk Ekonomi & NTV Ekonomi)
RSS_URLS = [
    "https://www.haberturk.com/rss/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss"
]

keywords = ["akaryakıt", "benzin", "motorin", "lpg", "zam", "indirim", "fiyat", "ekonomi", "petrol", "dolar"]

added_count = 0

for rss_url in RSS_URLS:
    print(f"\n--- RSS Adresinden veriler çekiliyor: {rss_url} ---")
    feed = feedparser.parse(rss_url)
    print(f"Toplam bulunan haber sayısı: {len(feed.entries)}")

    for entry in feed.entries[:20]:
        title = entry.title
        link = entry.link
        
        # Kelime eşleşmesi kontrolü (küçük harfe çevirerek)
        matched = any(kw in title.lower() for kw in keywords)
        
        if matched:
            print(f"-> Eşleşme bulundu! Ekleniyor: {title}")
            try:
                # Veritabanına kayıt
                data = {"title": title, "url": link}
                supabase.table("news").insert(data).execute()
                added_count += 1
            except Exception as e:
                # Mükerrer (zaten var olan) kayıtta hata vermemesi için
                print(f"Bilgi/Kayıt Notu: {e}")

print(f"\nİşlem tamamlandı. Eklenen toplam yeni haber sayısı: {added_count}")
