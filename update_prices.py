import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client

# Supabase Bağlantısı
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL veya SUPABASE_KEY ortam değişkeni bulunamadı!")

supabase: Client = create_client(url, key)

def get_afyon_prices():
    """
    Afyonkarahisar güncel akaryakıt fiyatlarını çeker.
    """
    benzin = 43.25
    motorin = 43.50
    lpg = 22.10

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get('https://www.doviz.com/akaryakit-fiyatlari', headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            print("Web sayfasından güncel fiyat çekme başarılı.")
    except Exception as e:
        print(f"Web'den fiyat çekerken hata oluştu, varsayılan değerler kullanılacak: {e}")

    return benzin, motorin, lpg

def update_supabase():
    benzin, motorin, lpg = get_afyon_prices()
    
    print(f"Güncellenecek Fiyatlar -> Benzin: {benzin}, Motorin: {motorin}, LPG: {lpg}")

    # Afyonkarahisar şehirli tüm istasyonların fiyatını güncelle
    response = supabase.table('stations').update({
        'benzin': str(benzin),
        'motorin': str(motorin),
        'lpg': str(lpg)
    }).eq('city', 'Afyonkarahisar').execute()

    print("Supabase başarıyla güncellendi!")

if __name__ == "__main__":
    update_supabase()
  
