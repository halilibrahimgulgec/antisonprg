import sqlite3

def find_outliers_and_top_records():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    print("-" * 50)
    print("En yüksek 10 yakıt alımı kaydı:")
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, satir_tutari 
        FROM yakit 
        ORDER BY yakit_miktari DESC 
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"Plaka: {row[0]:<15} | Tarih: {row[1]:<12} | Miktar: {row[2]:.2f} | Tutar: {row[3]:.2f}")
        
    print("-" * 50)
    # Çok yüksek veya çok düşük fiyatlar
    print("Birim fiyatı sıra dışı olan kayıtlar (Örn: > 50 TL veya < 10 TL):")
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, birim_fiyat 
        FROM yakit 
        WHERE birim_fiyat > 50 OR birim_fiyat < 10
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"Plaka: {row[0]:<15} | Tarih: {row[1]:<12} | Miktar: {row[2]:.2f} | Fiyat: {row[3]:.2f}")
        
    conn.close()

if __name__ == "__main__":
    find_outliers_and_top_records()
