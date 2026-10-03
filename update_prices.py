import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_doviz_prices():
    url = "https://www.doviz.com/akaryakit-fiyatlari"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print("Döviz.com hatası:", response.status_code)
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        prices = {}
        
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                brand = cols[0].text.strip().upper()
                benzin = cols[1].text.strip().replace('₺', '').replace(',', '.').strip()
                motorin = cols[2].text.strip().replace('₺', '').replace(',', '.').strip()
                lpg = cols[3].text.strip().replace('₺', '').replace(',', '.').strip()
                
                prices[brand] = {
                    'benzin': benzin,
                    'motorin': motorin,
                    'lpg': lpg
                }
        return prices
    except Exception as e:
        print("Hata:", e)
        return None

def main():
    doviz_data = fetch_doviz_prices()
    if not doviz_data:
        print("Fiyat verisi çekilemedi.")
        return

    # doviz_prices tablosunu temizleyip yeni marka fiyatlarını ekleyelim
    try:
        supabase.table('doviz_prices').delete().neq('id', 0).execute()
    except Exception as e:
        print("Temizleme uyarısı:", e)
    
    for brand, pdata in doviz_data.items():
        supabase.table('doviz_prices').insert({
            'brand': brand,
            'benzin': pdata['benzin'],
            'motorin': pdata['motorin'],
            'lpg': pdata['lpg']
        }).execute()
        print(f"Eklendi -> {brand}: {pdata}")

if __name__ == "__main__":
    main()
    
