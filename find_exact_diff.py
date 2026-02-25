import sqlite3

def find_exact_diff():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    # 1. 'deneme', 'test' içeren plakalar veya notlar
    print("-" * 50)
    cursor.execute("SELECT plaka, SUM(yakit_miktari) FROM yakit WHERE plaka LIKE '%TEST%' OR plaka LIKE '%DENEME%' GROUP BY plaka")
    for row in cursor.fetchall():
        print(f"Deneme Plaka: {row[0]} | Miktar: {row[1]}")

    # 2. Aktif - AdBlue hariç toplamdan 1088.95 çıkaracak plakalar var mı?
    # Bu farka en yakın tekil plaka toplamlarını bulalım
    cursor.execute("""
        SELECT a.plaka, SUM(y.yakit_miktari) as t
        FROM yakit y 
        JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 AND (y.stok_adi != 'ADBLUE' OR y.stok_adi IS NULL)
        GROUP BY a.plaka
        HAVING t BETWEEN 1000 AND 1200
    """)
    print("\n1088.95'e yakın (1000-1200) plaka toplamları:")
    for row in cursor.fetchall():
        print(f"Plaka: {row[0]} | Toplam: {row[1]}")

    # 3. Mükerrerleri (tekrar hesaplanan) - AdBlue haricindekiler
    cursor.execute("""
        SELECT SUM((tekrar-1) * yakit_miktari) FROM (
            SELECT plaka, islem_tarihi, yakit_miktari, km_bilgisi, COUNT(*) as tekrar
            FROM yakit 
            WHERE (stok_adi != 'ADBLUE' OR stok_adi IS NULL)
            GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
            HAVING tekrar > 1
        )
    """)
    mot_dup = cursor.fetchone()[0] or 0
    print(f"\nMotorin/None Mükerrer Toplamı: {mot_dup:.2f}")
    
    conn.close()

if __name__ == "__main__":
    find_exact_diff()
