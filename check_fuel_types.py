import sqlite3

def check_fuel_by_type():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    print("-" * 50)
    # AKTİF araçların tipine göre dağılımı
    cursor.execute("""
        SELECT a.arac_tipi, SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 
        GROUP BY a.arac_tipi
    """)
    print("Aktif araçların tipine göre yakıt toplamları:")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]}")
        
    print("-" * 50)
    conn.close()

if __name__ == "__main__":
    check_fuel_by_type()
