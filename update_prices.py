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
            print("Döviz.com bağlantı hatası:", response.status_code)
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
        print("Scraping Hatası:", e)
        return None

def main():
    doviz_data = fetch_doviz_prices()
    if not doviz_data:
        print("Döviz.com'dan fiyat verisi çekilemedi.")
        return

    print("Döviz.com'dan çekilen güncel fiyatlar:", doviz_data)

    # Supabase veritabanındaki kayıtları güncelle
    response = supabase.table('stations').select('*').execute()
    stations = response.data

    for station in stations:
        st_name = station.get('name', '').upper()
        matched = None
        
        for brand, pdata in doviz_data.items():
            if brand in st_name or st_name in brand:
                matched = pdata
                break
        
        # Marka eşleşmezse ortalama fiyat bilgisini bas
        if not matched and len(doviz_data) > 0:
            matched = list(doviz_data.values())[0]

        if matched:
            supabase.table('stations').update({
                'benzin': matched['benzin'],
                'motorin': matched['motorin'],
                'lpg': matched['lpg']
            }).eq('id', station['id']).execute()
            print(f"Güncellendi -> {station['name']}: {matched}")

if __name__ == "__main__":
    main()
    
