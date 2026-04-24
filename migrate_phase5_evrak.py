import sqlite3
import os

def migrate():
    db_path = 'kargo_data.db'
    if not os.path.exists(db_path):
        print(f"Veritabanı bulunamadı: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Evraklar tablosunu oluştur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sofor_evraklari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sofor_id INTEGER,
                plaka TEXT NOT NULL,
                evrak_tipi TEXT NOT NULL,
                aciklama TEXT,
                fotograf_yolu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sofor_id) REFERENCES soforler(id)
            )
        ''')
        print("✅ sofor_evraklari tablosu basariyla olusturuldu.")
        
        conn.commit()
    except Exception as e:
        print(f"❌ Hata olustu: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Evraklar tablosu migration islemi basliyor...")
    migrate()
    print("Migration tamamlandi.")
