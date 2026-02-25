
import sqlite3

def create_bakim_table():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bakim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            bakim_tipi TEXT NOT NULL,
            yapilan_islem TEXT,
            tarih DATE NOT NULL,
            km INTEGER,
            maliyet REAL,
            bir_sonraki_bakim_km INTEGER,
            bir_sonraki_bakim_tarih DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Bakim tablosu olusturuldu.")

if __name__ == "__main__":
    create_bakim_table()
