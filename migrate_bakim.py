import sqlite3

db_path = 'c:/Users/User/Desktop/boltson12112025_1/project/kargo_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE bakim ADD COLUMN durum TEXT DEFAULT 'Tamamlandı'")
    print('Added column durum to bakim table.')
except sqlite3.OperationalError as e:
    print('Error or column already exists:', e)

conn.commit()
conn.close()
