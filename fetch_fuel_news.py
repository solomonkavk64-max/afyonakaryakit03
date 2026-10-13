import os
import feedparser
from supabase import create_client

# GitHub Secrets üzerinden Supabase bağlantı bilgileri
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Takip edilen RSS kaynakları (Ekonomi / Gündem)
rss_urls = [
    "https://www.haberturk.com/rss/kategori/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss"
]

def fetch_fresh_news():
    news_list = []
    seen_titles = set()
    
    for url in rss_urls:
        feed = feedparser.parse(url)
        # Her kaynaktan en taze ilk 8 haberi alıyoruz
        for entry in feed.entries[:8]:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()
            link = entry.get('link', '').strip()
            
            if title and link and title not in seen_titles:
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
        # Tablodaki tüm eski haberleri siliyoruz, liste sadece en güncel taze haberlerle dolacak
        supabase.table('news').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Eski haberler silinirken hata oluştu: {e}")

    print("📥 Güncel haberler çekiliyor...")
    fresh_news = fetch_fresh_news()

    if fresh_news:
        print(f"✨ Supabase'e eklenen toplam güncel haber sayısı: {len(fresh_news)}")
        response = supabase.table('news').insert(fresh_news).execute()
        print("İşlem başarıyla tamamlandı!")
    else:
        print("Eklenecek yeni haber bulunamadı.")

if __name__ == "__main__":
    update_news_table()
