import sqlite3

def check_fuel_by_price_and_others():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    print("-" * 50)
    # 1. Sadece fiyatı (satir_tutari) 0'dan büyük olanların toplamı
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 AND y.satir_tutari > 0
    """)
    priced_total = cursor.fetchone()[0] or 0
    print(f"1. Fiyatlı (satir_tutari > 0) yakıt toplamı: {priced_total:.2f}")

    # 2. Fiyatı 0 veya NULL olanların toplamı
    cursor.execute("""
        SELECT SUM(y.yakit_miktari) 
        FROM yakit y 
        INNER JOIN araclar a ON y.plaka = a.plaka 
        WHERE a.aktif = 1 AND (y.satir_tutari <= 0 OR y.satir_tutari IS NULL)
    """)
    unpriced_total = cursor.fetchone()[0] or 0
    print(f"2. Fiyatsız veya 0 TL olan yakıt toplamı: {unpriced_total:.2f}")

    # 3. Toplam (Kontrol)
    print(f"3. Toplam (1+2): {priced_total + unpriced_total:.2f}")
    
    # Farkı kontrol et (Homepage: 696,469.83 - User: 687,382.88 = 9,086.95)
    print(f"\nBeklenen Fark: 9086.95")
    
    conn.close()

if __name__ == "__main__":
    check_fuel_by_price_and_others()
