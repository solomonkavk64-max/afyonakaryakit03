import feedparser
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# RSS Akış Adresi
RSS_URL = "https://www.trthaber.com/xml/rss/sondakika.xml"

print(f"RSS Adresinden veriler çekiliyor: {RSS_URL}")
feed = feedparser.parse(RSS_URL)
print(f"Toplam bulunan haber sayısı: {len(feed.entries)}")

keywords = ["akaryakıt", "benzin", "motorin", "lpg", "zam", "indirim", "akaryakıt fiyatları", "ekonomi"]

added_count = 0

for entry in feed.entries[:15]:
    title = entry.title
    link = entry.link
    print(f"İncelenen Haber: {title}")
    
    # Kelime eşleşmesi kontrolü
    matched = any(kw in title.lower() for kw in keywords)
    
    if matched:
        print(f"-> Eşleşme bulundu! Ekleniyor: {title}")
        try:
            # Supabase ekleme işlemi (tablo yapına göre)
            data = {"title": title, "url": link}
            supabase.table("news").insert(data).execute()
            added_count += 1
        except Exception as e:
            print(f"Supabase kayıt hatası: {e}")

print(f"İşlem tamamlandı. Eklenen toplam haber: {added_count}")
