import sqlite3

def check_all_owners():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    print("-" * 50)
    cursor.execute("SELECT sahip, aktif, COUNT(*) FROM araclar GROUP BY sahip, aktif")
    print(f"{'Sahip':<15} | {'Aktif':<5} | {'Adet'}")
    print("-" * 30)
    for row in cursor.fetchall():
        print(f"{str(row[0]):<15} | {str(row[1]):<5} | {row[2]}")
        
    conn.close()

if __name__ == "__main__":
    check_all_owners()
