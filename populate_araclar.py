import sqlite3

DATABASE_PATH = 'kargo_data.db'

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
if cursor.fetchone() is None:
    print("❌ Hata: 'araclar' tablosu bulunamadı!")
    print("➡️  Önce 'python create_araclar_table.py' komutunu çalıştırın.")
    conn.close()
    exit(1)

plakalar = set()

cursor.execute('SELECT DISTINCT plaka FROM yakit WHERE plaka IS NOT NULL AND plaka != ""')
for row in cursor.fetchall():
    plakalar.add(row[0])

cursor.execute('SELECT DISTINCT plaka FROM agirlik WHERE plaka IS NOT NULL AND plaka != ""')
for row in cursor.fetchall():
    plakalar.add(row[0])

cursor.execute('SELECT DISTINCT plaka FROM arac_takip WHERE plaka IS NOT NULL AND plaka != ""')
for row in cursor.fetchall():
    plakalar.add(row[0])

print(f'📋 Veritabanında toplam {len(plakalar)} farklı plaka bulundu')

eklenen = 0
zaten_var = 0

for plaka in sorted(plakalar):
    cursor.execute('SELECT id FROM araclar WHERE plaka = ?', (plaka,))
    if cursor.fetchone() is not None:
        zaten_var += 1
        continue

    try:
        cursor.execute('''
            INSERT INTO araclar (plaka, sahip, arac_tipi, aktif)
            VALUES (?, 'BİZİM', 'KARGO ARACI', 1)
        ''', (plaka,))
        eklenen += 1
    except Exception as e:
        print(f'⚠️  {plaka} eklenirken hata: {e}')

conn.commit()
conn.close()

print(f'\n✅ İşlem tamamlandı!')
print(f'   • Yeni eklenen: {eklenen} araç')
print(f'   • Zaten kayıtlı: {zaten_var} araç')
print(f'   • Toplam: {eklenen + zaten_var} araç')

if eklenen > 0:
    print(f'\n📝 {eklenen} araç "BİZİM" ve "KARGO ARACI" olarak aktif şekilde eklendi.')
    print('   Araç Yönetimi sayfasından düzenleyebilirsiniz.')
