import sqlite3

def check_duplicate_records():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    # Aynı plaka, tarih, miktar ve km'ye sahip kayıtları bul
    cursor.execute("""
        SELECT plaka, islem_tarihi, yakit_miktari, km_bilgisi, COUNT(*) as tekrar
        FROM yakit 
        GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
        HAVING tekrar > 1
        ORDER BY tekrar DESC
    """)
    
    duplicates = cursor.fetchall()
    if not duplicates:
        print("Mükerrer kayıt bulunamadı.")
    else:
        print(f"Toplam {len(duplicates)} grupta mükerrer kayıt bulundu.")
        total_duplicate_fuel = 0
        for row in duplicates:
            # (Tekrar - 1) kadar olan yakıt miktarı fazlalıktır
            extra_fuel = (row[4] - 1) * row[2]
            total_duplicate_fuel += extra_fuel
            # print(f"Plaka: {row[0]} | Tarih: {row[1]} | Miktar: {row[2]} | Tekrar: {row[4]} | Fazlalık: {extra_fuel:.2f}")
        
        print(f"\nMükerrer kayıtlardan kaynaklanan toplam fazla yakıt: {total_duplicate_fuel:.2f} L")
        
    conn.close()

if __name__ == "__main__":
    check_duplicate_records()
