import os
import requests
import feedparser
from supabase import create_client, Client

# Supabase Bilgileri (GitHub Secrets'tan otomatik alınacak)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_save_news():
    # Güvenilir bir RSS kaynağı (Örn: TRT Haber Ekonomi)
    rss_url = "https://www.trthaber.com/ekonomi_haberleri.rss" 
    
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries[:5]: # Son 5 habere bak
        title = entry.title
        summary = entry.summary if 'summary' in entry else ""
        
        # Akaryakıt, benzin veya motorin ile ilgili anahtar kelimeler geçiyor mu?
        if any(keyword in title.lower() for keyword in ["akaryakıt", "benzin", "motorin", "lpg", "zam", "indirim"]):
            
            # Bu haber daha önce eklenmiş mi kontrol et (Mükerrer kayıt önleme)
            existing = supabase.from_('news').select('id').eq('title', title).execute()
            
            if not existing.data:
                # Supabase'e yeni haberi ekle
                supabase.from_('news').insert({
                    "title": title,
                    "content": summary
                }).execute()
                print(f"Yeni akaryakıt haberi eklendi: {title}")

if __name__ == "__main__":
    fetch_and_save_news()
