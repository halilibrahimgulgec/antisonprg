import sqlite3
import os

DB_PATH = 'kargo_data.db'

def migrate_phase5():
    if not os.path.exists(DB_PATH):
        print(f"Hata: {DB_PATH} bulunamadı!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Seferler Tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seferler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sofor_id INTEGER,
                plaka TEXT,
                baslangic_zaman TIMESTAMP,
                bitis_zaman TIMESTAMP,
                baslangic_km INTEGER,
                bitis_km INTEGER,
                durum TEXT DEFAULT 'Aktif',
                FOREIGN KEY (sofor_id) REFERENCES soforler (id)
            )
        ''')

        # 2. Yakıt ve Kaza/Arıza bildirimleri için şoför panelinden gelen veriler zaten "yakit" ve "hasarlar" tablolarına atılabilir.
        # Konum bilgisini "hasarlar" tablosuna eklemekte fayda var (Alter table).
        try:
            cursor.execute("ALTER TABLE hasarlar ADD COLUMN konum_enlem REAL")
            cursor.execute("ALTER TABLE hasarlar ADD COLUMN konum_boylam REAL")
            cursor.execute("ALTER TABLE hasarlar ADD COLUMN fotograf_yolu TEXT")
            print("'hasarlar' tablosuna PWA için konum ve fotoğraf sütunları eklendi.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Sütunlar zaten var
            else:
                print(f"Uyarı (hasarlar): {e}")

        # Aynı şekilde yakıt fişi için de "yakit" tablosuna fiş fotoğrafı sütunu ekleyelim
        try:
            cursor.execute("ALTER TABLE yakit ADD COLUMN fis_fotograf_yolu TEXT")
            cursor.execute("ALTER TABLE yakit ADD COLUMN sofor_id INTEGER")
            print("'yakit' tablosuna PWA için fiş fotoğrafı ve sofor id sütunları eklendi.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Sütunlar zaten var
            else:
                print(f"Uyarı (yakit): {e}")

        conn.commit()
        conn.close()
        print("Asama 5 (Sofor Paneli - Seferler) veritabani tablolari basariyla olusturuldu/guncellendi!")
    except Exception as e:
        print(f"Veritabani modifikasyonu sirasinda hata: {e}")

if __name__ == '__main__':
    migrate_phase5()
