import sqlite3

def clean_database():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    # 1. 1500L'lik hatalı kayıtları sil (34HR8686 ve 34NBD172)
    print("Hatalı (1500L) kayıtlar siliniyor...")
    cursor.execute("DELETE FROM yakit WHERE yakit_miktari = 1500 AND (satir_tutari = 0 OR satir_tutari IS NULL)")
    print(f"{cursor.rowcount} adet hatalı kayıt silindi.")

    # 2. Mükerrer kayıtları temizle (Sadece birer tane bırak)
    print("\nMükerrer kayıtlar temizleniyor...")
    # Rowid kullanarak mükerrerlerden sadece birini tut, diğerlerini sil
    cursor.execute("""
        DELETE FROM yakit 
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM yakit
            GROUP BY plaka, islem_tarihi, yakit_miktari, km_bilgisi
        )
    """)
    print(f"{cursor.rowcount} adet mükerrer kayıt silindi.")

    conn.commit()
    conn.close()
    print("\nTemizlik tamamlandı.")

if __name__ == "__main__":
    clean_database()
