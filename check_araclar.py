import sqlite3

conn = sqlite3.connect('kargo_data.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM araclar')
print(f'Toplam araç: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM araclar WHERE aktif=1')
print(f'Aktif araç: {cursor.fetchone()[0]}')

cursor.execute("SELECT COUNT(*) FROM araclar WHERE arac_tipi='KARGO ARACI'")
print(f'Kargo araçları: {cursor.fetchone()[0]}')

cursor.execute("SELECT COUNT(*) FROM araclar WHERE aktif=1 AND arac_tipi='KARGO ARACI'")
print(f'Aktif kargo araçları: {cursor.fetchone()[0]}')

print('\nİlk 5 araç:')
cursor.execute('SELECT plaka, arac_tipi, aktif FROM araclar LIMIT 5')
for row in cursor.fetchall():
    print(f'  Plaka: {row[0]}, Tip: {row[1]}, Aktif: {row[2]}')

conn.close()
