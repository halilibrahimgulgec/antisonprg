import sqlite3

DATABASE_PATH = 'kargo_data.db'

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS araclar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plaka TEXT UNIQUE NOT NULL,
    sahip TEXT NOT NULL CHECK(sahip IN ('BİZİM', 'TAŞERON')),
    arac_tipi TEXT NOT NULL CHECK(arac_tipi IN ('KARGO ARACI', 'İŞ MAKİNESİ', 'DİĞER')),
    aktif INTEGER NOT NULL DEFAULT 1 CHECK(aktif IN (0, 1)),
    notlar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("✅ 'araclar' tablosu oluşturuldu!")
