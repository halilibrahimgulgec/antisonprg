import sqlite3

def test_scenarios():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    target = 687382.88
    print(f"Hedef Rakam (Kullanıcı): {target}\n")
    
    # Senaryo 1: Tüm Aktif Araçlar (Homepage)
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1
    """)
    s1 = cursor.fetchone()[0] or 0
    print(f"1. Tüm Aktif Araçlar: {s1:.2f} (Fark: {s1-target:.2f})")

    # Senaryo 2: Aktif Araçlar - AdBlue Hariç
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 AND (y.stok_adi != 'ADBLUE' OR y.stok_adi IS NULL)
    """)
    s2 = cursor.fetchone()[0] or 0
    print(f"2. Aktif Araçlar (AdBlue Hariç): {s2:.2f} (Fark: {s2-target:.2f})")

    # Senaryo 3: Aktif Araçlar - Binek Hariç
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 AND a.arac_tipi NOT LIKE '%BNEK%'
    """)
    s3 = cursor.fetchone()[0] or 0
    print(f"3. Aktif Araçlar (Binek Hariç): {s3:.2f} (Fark: {s3-target:.2f})")

    # Senaryo 4: Aktif Araçlar - Mükerrer Hariç (Tahmini)
    # Önce mukerrerleri bulalım
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, km_bilgisi, COUNT(*) as tekrar
        FROM yakit 
        GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
        HAVING tekrar > 1
    """)
    dup_fuel = sum((row[4]-1)*row[2] for row in cursor.fetchall())
    s4 = s1 - dup_fuel
    print(f"4. Aktif Araçlar (Mükerrer Hariç): {s4:.2f} (Fark: {s4-target:.2f})")

    # Senaryo 5: Aktif Araçlar - Mükerrer Hariç - AdBlue Hariç
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, km_bilgisi, COUNT(*) as tekrar
        FROM yakit 
        WHERE stok_adi = 'ADBLUE'
        GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
        HAVING tekrar > 1
    """)
    adblue_dup = sum((row[4]-1)*row[2] for row in cursor.fetchall())
    s5 = s2 - (dup_fuel - adblue_dup) # Sadece motorin mükerrerlerini düş
    print(f"5. Aktif - Mükerrer(Mot) - AdBlue Hariç: {s5:.2f} (Fark: {s5-target:.2f})")

    # Senaryo 6: 1500L hatasını çıkaralım (S1 üzerinden)
    s6 = s1 - 3000
    print(f"6. Aktif Araçlar (3000L Hata Hariç): {s6:.2f} (Fark: {s6-target:.2f})")

    conn.close()

if __name__ == "__main__":
    test_scenarios()
