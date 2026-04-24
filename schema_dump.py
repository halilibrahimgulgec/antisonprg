import sqlite3

conn = sqlite3.connect('kargo_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
for row in cursor.fetchall():
    print(f"--- {row[0]} ---")
    print(row[1])
conn.close()
