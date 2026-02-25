import sqlite3
import json

def inspect_vehicle(plaka):
    conn = sqlite3.connect('kargo_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Tüm kayıtları al
    cursor.execute('SELECT islem_tarihi, km_bilgisi, km_fark, yakit_miktari FROM yakit WHERE plaka=? ORDER BY islem_tarihi', (plaka,))
    rows = [dict(r) for r in cursor.fetchall()]
    
    print(f"--- Records for {plaka} ---")
    for r in rows:
        print(f"{r['islem_tarihi']} | KM: {r['km_bilgisi']} | Fark: {r['km_fark']} | Fuel: {r['yakit_miktari']} L")
    
    # Yeni Mantık: Makul farkları topla
    valid_diffs = [r['km_fark'] for r in rows if r['km_fark'] is not None and 0 < r['km_fark'] < 2000]
    toplam_km_yeni = sum(valid_diffs)
    
    print(f"\nYENİ MANTIK (Filtrelenmiş):")
    print(f"Geçerli Fark Sayısı: {len(valid_diffs)}")
    print(f"Toplam KM (Yeni): {toplam_km_yeni}")
    
    total_fuel = sum(r['yakit_miktari'] for r in rows if r['yakit_miktari'])
    if toplam_km_yeni > 0:
        print(f"Yeni Tüketim (L/100km): {total_fuel / toplam_km_yeni * 100:.2f}")
    
    conn.close()

if __name__ == "__main__":
    inspect_vehicle("46AJH284")
