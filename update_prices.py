import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_doviz_com_prices():
    url = "https://www.doviz.com/akaryakit-fiyatlari"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Döviz.com veri çekme hatası:", response.status_code)
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    prices = {}
    
    # Doviz.com tablo parsing işlemi
    rows = soup.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            brand = cols[0].text.strip()
            benzin = cols[1].text.strip().replace('₺', '').replace(',', '.')
            motorin = cols[2].text.strip().replace('₺', '').replace(',', '.')
            lpg = cols[3].text.strip().replace('₺', '').replace(',', '.')
            prices[brand] = {'benzin': benzin, 'motorin': motorin, 'lpg': lpg}
            
    return prices

def update_database():
    doviz_prices = fetch_doviz_com_prices()
    if not doviz_prices:
        print("Fiyat verisi alınamadı.")
        return

    # Veritabanındaki tüm istasyonları güncelle
    response = supabase.table('stations').select('*').execute()
    stations = response.data

    for station in stations:
        brand = station.get('brand', 'Shell')
        
        # Doviz.com verilerinde eşleşen marka var mı kontrol et
        matched_price = None
        for key in doviz_prices:
            if key.lower() in brand.lower() or brand.lower() in key.lower():
                matched_price = doviz_prices[key]
                break
        
        if matched_price:
            supabase.table('stations').update({
                'benzin': matched_price['benzin'],
                'motorin': matched_price['motorin'],
                'lpg': matched_price['lpg']
            }).eq('id', station['id']).execute()
            print(f"{station['name']} güncellendi.")

if __name__ == "__main__":
    update_database()
    
