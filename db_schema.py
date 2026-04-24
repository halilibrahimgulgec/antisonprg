import sqlite3

conn = sqlite3.connect('kargo_data.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('agirlik', 'bakim', 'yakit');")
for row in cursor.fetchall():
    print(row[0])
    print("-" * 50)
conn.close()
