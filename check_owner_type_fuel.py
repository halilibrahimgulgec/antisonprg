import sqlite3

def check_fuel_by_owner_and_type():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.sahip, a.arac_tipi, SUM(y.yakit_miktari) as toplam
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 
        GROUP BY a.sahip, a.arac_tipi
        ORDER BY a.sahip, a.arac_tipi
    """)
    
    print(f"{'Sahip':<15} | {'Tip':<20} | {'Toplam Yakıt'}")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} | {row[1]:<20} | {row[2]:.2f}")
        
    conn.close()

if __name__ == "__main__":
    check_fuel_by_owner_and_type()
