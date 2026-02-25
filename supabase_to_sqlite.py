"""
Supabase PostgreSQL'den SQLite'a veri kopyalama (HTTP ile)
"""
import os
import sqlite3
import urllib.request
import json

# .env dosyasını manuel oku
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

env = load_env()

# Supabase bağlantısı
SUPABASE_URL = env.get('VITE_SUPABASE_URL')
SUPABASE_KEY = env.get('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ .env dosyasında SUPABASE bilgileri bulunamadı!")
    exit(1)

def fetch_data(table_name):
    """Supabase'den tüm tablo verisini çek (pagination ile)"""
    all_data = []
    offset = 0
    limit = 1000

    while True:
        url = f'{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit={limit}&offset={offset}'
        req = urllib.request.Request(url)
        req.add_header('apikey', SUPABASE_KEY)
        req.add_header('Authorization', f'Bearer {SUPABASE_KEY}')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Prefer', 'count=exact')

        try:
            with urllib.request.urlopen(req) as response:
                batch = json.loads(response.read().decode())
                if not batch or len(batch) == 0:
                    break
                all_data.extend(batch)
                print(f"   📥 {len(batch)} kayıt çekildi (toplam: {len(all_data)})")

                if len(batch) < limit:
                    break
                offset += limit
        except Exception as e:
            print(f"❌ Veri çekme hatası: {e}")
            break

    return all_data

# SQLite bağlantısı
db_path = 'kargo_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔄 Supabase'den SQLite'a veri kopyalanıyor...\n")

# 1. YAKIT TABLOSU
print("⛽ Yakıt verileri çekiliyor...")
try:
    yakit_data = fetch_data('yakit')

    if yakit_data and isinstance(yakit_data, list):
        for row in yakit_data:
            cursor.execute('''
                INSERT INTO yakit (plaka, islem_tarihi, saat, yakit_miktari, birim_fiyat,
                                   satir_tutari, stok_adi, km_bilgisi, km_fark, litre_km,
                                   toplam_yuk, ton_litre)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('plaka'),
                row.get('islem_tarihi'),
                row.get('saat'),
                row.get('yakit_miktari'),
                row.get('birim_fiyat'),
                row.get('satir_tutari'),
                row.get('stok_adi'),
                row.get('km_bilgisi'),
                row.get('km_fark'),
                row.get('litre_km'),
                row.get('toplam_yuk'),
                row.get('ton_litre')
            ))
        conn.commit()
        print(f"✅ {len(yakit_data)} yakıt kaydı kopyalandı")
    else:
        print("⚠️  Yakıt verisi yok")
except Exception as e:
    print(f"❌ Yakıt kopyalama hatası: {e}")

# 2. AĞIRLIK TABLOSU
print("\n⚖️  Ağırlık verileri çekiliyor...")
try:
    agirlik_data = fetch_data('agirlik')

    if agirlik_data and isinstance(agirlik_data, list):
        for row in agirlik_data:
            cursor.execute('''
                INSERT INTO agirlik (tarih, miktar, birim, net_agirlik, plaka,
                                     adres, islem_noktasi, cari_adi, ana_malzeme)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('tarih'),
                row.get('miktar'),
                row.get('birim'),
                row.get('net_agirlik'),
                row.get('plaka'),
                row.get('adres'),
                row.get('islem_noktasi'),
                row.get('cari_adi'),
                row.get('ana_malzeme')
            ))
        conn.commit()
        print(f"✅ {len(agirlik_data)} ağırlık kaydı kopyalandı")
    else:
        print("⚠️  Ağırlık verisi yok")
except Exception as e:
    print(f"❌ Ağırlık kopyalama hatası: {e}")

# 3. ARAÇ TAKİP TABLOSU
print("\n🚛 Araç takip verileri çekiliyor...")
try:
    arac_data = fetch_data('arac_takip')

    if arac_data and isinstance(arac_data, list):
        for row in arac_data:
            cursor.execute('''
                INSERT INTO arac_takip (plaka, sofor_adi, arac_gruplari, tarih,
                                        hareket_baslangic_tarihi, hareket_bitis_tarihi,
                                        baslangic_adresi, bitis_adresi, baslangic_koordinatlari,
                                        bitis_koordinatlari, baslangic_kilometre, bitis_kilometre,
                                        maksimum_hiz, toplam_kilometre, hareket_suresi,
                                        rolanti_suresi, park_suresi, toplam_asiri_hiz_alarmi,
                                        toplam_rolanti_alarmi, gunluk_yakit_tuketimi_l)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('plaka'),
                row.get('sofor_adi'),
                row.get('arac_gruplari'),
                row.get('tarih'),
                row.get('hareket_baslangic_tarihi'),
                row.get('hareket_bitis_tarihi'),
                row.get('baslangic_adresi'),
                row.get('bitis_adresi'),
                row.get('baslangic_koordinatlari'),
                row.get('bitis_koordinatlari'),
                row.get('baslangic_kilometre'),
                row.get('bitis_kilometre'),
                row.get('maksimum_hiz'),
                row.get('toplam_kilometre'),
                row.get('hareket_suresi'),
                row.get('rolanti_suresi'),
                row.get('park_suresi'),
                row.get('toplam_asiri_hiz_alarmi'),
                row.get('toplam_rolanti_alarmi'),
                row.get('gunluk_yakit_tuketimi_l')
            ))
        conn.commit()
        print(f"✅ {len(arac_data)} araç takip kaydı kopyalandı")
    else:
        print("⚠️  Araç takip verisi yok")
except Exception as e:
    print(f"❌ Araç takip kopyalama hatası: {e}")

conn.close()

print("\n" + "="*60)
print("✅ VERİ KOPYALAMA TAMAMLANDI!")
print("="*60)
print(f"📁 SQLite Veritabanı: {db_path}")
print("🚀 Flask'ı başlatın: python app.py")
print("="*60)
