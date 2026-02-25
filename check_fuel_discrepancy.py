import sqlite3

def check_fuel_sums():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    print("-" * 50)
    # 1. Ham Toplam (Filtresiz)
    cursor.execute("SELECT SUM(yakit_miktari) FROM yakit")
    raw_total = cursor.fetchone()[0]
    print(f"1. Ham 'yakit' tablosundaki tüm verilerin toplamı: {raw_total}")
    
    # 2. Sadece aktif olanların toplamı (Şu anki ana sayfa mantığı)
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1
    """)
    active_total = cursor.fetchone()[0]
    print(f"2. AKTİF (aktif=1) araçların yakıt toplamı: {active_total}")
    
    # 3. Bizim araçlar vs Taşeron (Aktif olanlar içinde)
    cursor.execute("""
        SELECT a.sahip, SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 
        GROUP BY a.sahip
    """)
    print("\n3. Sahip durumuna göre dağılım (Aktif araçlar):")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]}")
        
    # 4. Pasif araçların toplamı
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 0
    """)
    passive_total = cursor.fetchone()[0]
    print(f"\n4. PASİF (aktif=0) araçların yakıt toplamı: {passive_total}")

    # 5. Eslesmeyen (araclar tablosunda olmayan) plakalar
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        LEFT JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.plaka IS NULL
    """)
    null_arac_total = cursor.fetchone()[0]
    print(f"5. 'araclar' tablosunda kaydı olmayan plakaların yakıtı: {null_arac_total}")
    print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    check_fuel_sums()
