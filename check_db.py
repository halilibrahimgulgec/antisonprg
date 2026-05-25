import sqlite3
import sys

def check_db():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT plaka FROM yakit WHERE plaka LIKE '%46%AHR%076%' OR plaka LIKE '%46%ahr%076%';")
    rows = cursor.fetchall()
    print("Found plates matching 46 AHR 076:")
    for row in rows:
        print(row[0])
    
    print("\nSample plates:")
    cursor.execute("SELECT DISTINCT plaka FROM yakit LIMIT 10;")
    for row in cursor.fetchall():
        print(row[0])
        
    conn.close()

if __name__ == '__main__':
    check_db()
