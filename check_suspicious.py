import sqlite3

def check_suspicious_data():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    # 1. 1000 litreden fazla olan tek seferlik yakıt alımları
    print("-" * 50)
    print("1000 Litre Üzeri Tek Seferlik Alımlar:")
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari 
        FROM yakit 
        WHERE yakit_miktari > 1000
    """)
    rows = cursor.fetchall()
    abnormal_total = 0
    for row in rows:
        print(f"Plaka: {row[0]:<15} | Tarih: {row[1]:<12} | Miktar: {row[2]:.2f}")
        abnormal_total += row[2]
    print(f"Abnormal Toplam: {abnormal_total:.2f}")

    # 2. Mükerrerleri (tekrar hesaplanan)
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, km_bilgisi, COUNT(*) as tekrar
        FROM yakit 
        GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
        HAVING tekrar > 1
    """)
    duplicates = cursor.fetchall()
    dup_total = 0
    for row in duplicates:
        dup_total += (row[4] - 1) * row[2]
    print(f"\nMükerrerlerden Gelen Fazlalık: {dup_total:.2f}")

    # 3. Binek araçlardaki yüksek yakıtlar (> 200 Litre bir seferde binek için çoktur)
    print("\nBinek Araçlarda > 200L Alımlar:")
    cursor.execute("""
        SELECT y.plaka, y.islem_tarihi, y.yakit_miktari 
        FROM yakit y
        INNER JOIN araclar a ON y.plaka = a.plaka
        WHERE a.arac_tipi LIKE '%BNEK%' AND y.yakit_miktari > 200
    """)
    binek_high = cursor.fetchall()
    binek_high_total = 0
    for row in binek_high:
        print(f"Plaka: {row[0]:<15} | Tarih: {row[1]:<12} | Miktar: {row[2]:.2f}")
        binek_high_total += row[2]
    print(f"Binek Yüksek Toplam: {binek_high_total:.2f}")

    conn.close()

if __name__ == "__main__":
    check_suspicious_data()
