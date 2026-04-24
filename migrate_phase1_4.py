import sqlite3
import os

DATABASE_PATH = 'kargo_data.db'

def setup_phase1_to_4_tables():
    if not os.path.exists(DATABASE_PATH):
        print(f"Hata: {DATABASE_PATH} veritabanı bulunamadı.")
        return False

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 1. Aşama: araclar tablosuna yeni sütunlar
        print("Araclar tablosu güncelleniyor...")
        columns_to_add = [
            ("sigorta_tarihi", "DATE"),
            ("muayene_tarihi", "DATE"),
            ("kasko_tarihi", "DATE")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE araclar ADD COLUMN {col_name} {col_type}")
                print(f" - Sütun eklendi: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f" - Sütun zaten mevcut: {col_name}")
                else:
                    print(f" - Hata ({col_name}): {e}")

        # 2. Aşama: soforler tablosu
        print("soforler tablosu oluşturuluyor...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS soforler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT NOT NULL,
            telefon TEXT,
            tc_no TEXT,
            aktif INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 3. Aşama: cezalar tablosu
        print("cezalar tablosu oluşturuluyor...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cezalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            sofor_id INTEGER,
            tarih DATE NOT NULL,
            tutar REAL NOT NULL,
            aciklama TEXT,
            odeme_durumu TEXT DEFAULT 'Ödenmedi',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sofor_id) REFERENCES soforler(id)
        )
        ''')

        # 3. Aşama: hasarlar tablosu
        print("hasarlar tablosu oluşturuluyor...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hasarlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            sofor_id INTEGER,
            tarih DATE NOT NULL,
            tutar REAL NOT NULL,
            aciklama TEXT,
            sigorta_karsiladi_mi INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sofor_id) REFERENCES soforler(id)
        )
        ''')

        # 4. Aşama: lastikler tablosu
        print("lastikler tablosu oluşturuluyor...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lastikler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marka TEXT,
            ebat TEXT,
            seri_no TEXT,
            fiyat REAL,
            alinma_tarihi DATE,
            aktif INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 4. Aşama: arac_lastik_durumu tablosu
        print("arac_lastik_durumu tablosu oluşturuluyor...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS arac_lastik_durumu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            lastik_id INTEGER NOT NULL,
            takilma_tarihi DATE,
            takilma_km INTEGER,
            pozisyon TEXT,
            sokulme_tarihi DATE,
            sokulme_km INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lastik_id) REFERENCES lastikler(id)
        )
        ''')

        conn.commit()
        print("\nTüm tablolar ve sütunlar başarıyla eklendi!")
        return True

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_phase1_to_4_tables()
