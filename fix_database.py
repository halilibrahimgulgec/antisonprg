#!/usr/bin/env python3
"""
Veritabanını temizle ve boş tablolar oluştur
"""
import os
import sqlite3

db_path = 'kargo_data.db'

# Eski veritabanını sil
if os.path.exists(db_path):
    print(f"🗑️  Eski veritabanı siliniyor: {db_path}")
    os.remove(db_path)

print(f"📦 Yeni veritabanı oluşturuluyor: {db_path}")

# Yeni bağlantı
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabloları oluştur
print("📋 Tablolar oluşturuluyor...")

cursor.execute('''
CREATE TABLE yakit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plaka TEXT,
    islem_tarihi TEXT,
    saat TEXT,
    yakit_miktari REAL,
    birim_fiyat REAL,
    satir_tutari REAL,
    stok_adi TEXT,
    km_bilgisi REAL,
    km_fark REAL,
    litre_km REAL,
    toplam_yuk REAL,
    ton_litre REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE agirlik (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih TEXT,
    miktar REAL,
    birim TEXT,
    net_agirlik REAL,
    plaka TEXT,
    adres TEXT,
    islem_noktasi TEXT,
    cari_adi TEXT,
    ana_malzeme TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE arac_takip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plaka TEXT,
    sofor_adi TEXT,
    arac_gruplari TEXT,
    tarih TEXT,
    hareket_baslangic_tarihi TEXT,
    hareket_bitis_tarihi TEXT,
    baslangic_adresi TEXT,
    bitis_adresi TEXT,
    baslangic_koordinatlari TEXT,
    bitis_koordinatlari TEXT,
    baslangic_kilometre REAL,
    bitis_kilometre REAL,
    maksimum_hiz REAL,
    toplam_kilometre REAL,
    hareket_suresi TEXT,
    rolanti_suresi TEXT,
    park_suresi TEXT,
    toplam_asiri_hiz_alarmi INTEGER,
    toplam_rolanti_alarmi INTEGER,
    gunluk_yakit_tuketimi_l REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE araclar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plaka TEXT UNIQUE NOT NULL,
    sahip TEXT DEFAULT 'BİZİM',
    arac_tipi TEXT DEFAULT 'KARGO ARACI',
    aktif INTEGER DEFAULT 1,
    notlar TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

print("✅ Tablolar oluşturuldu (boş)")

conn.commit()

print(f"\n{'='*60}")
print(f"✅ BOŞ VERİTABANI OLUŞTURULDU!")
print(f"{'='*60}")
print(f"📁 Dosya: {db_path}")
print(f"📊 Tablolar: yakit, agirlik, arac_takip, araclar (boş)")
print(f"{'='*60}")
print(f"📋 Veri eklemek için:")
print(f"   1. Excel dosyalarınızı proje klasörüne koyun")
print(f"   2. python excel_to_sqlite.py komutunu çalıştırın")
print(f"{'='*60}")
print(f"🚀 Flask'ı başlatın: python app.py")
print(f"{'='*60}\n")

conn.close()
