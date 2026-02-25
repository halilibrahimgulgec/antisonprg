import sqlite3

def list_all_vehicle_fuel():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.plaka, a.arac_tipi, a.sahip, SUM(y.yakit_miktari) as toplam
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 
        GROUP BY a.plaka, a.arac_tipi, a.sahip
        ORDER BY toplam DESC
    """)
    
    print(f"{'Plaka':<15} | {'Tip':<15} | {'Sahip':<10} | {'Yakıt':<10}")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} | {row[1]:<15} | {row[2]:<10} | {row[3]:<10.2f}")
        
    conn.close()

if __name__ == "__main__":
    list_all_vehicle_fuel()
