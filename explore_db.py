import sqlite3
import pandas as pd

def check_plate_data(plaka):
    conn = sqlite3.connect('kargo_data.db')
    
    print(f"\n--- {plaka} Kantar (agirlik) Tablosu Verileri ---")
    query = "SELECT * FROM agirlik WHERE plaka = ?"
    df = pd.read_sql_query(query, conn, params=(plaka,))
    
    if df.empty:
        print("Kantar kaydı bulunamadı.")
        # Benzer plakaları ara
        print("\nBenzer plakalar aranıyor...")
        similar_query = "SELECT DISTINCT plaka FROM agirlik WHERE plaka LIKE ?"
        similar = pd.read_sql_query(similar_query, conn, params=(f"%{plaka[-3:]}%",))
        print(similar)
    else:
        print(f"Toplam {len(df)} kayıt bulundu.")
        print("\nBirim Dağılımı:")
        print(df['birim'].value_counts())
        print("\nMalzeme Dağılımı:")
        print(df['ana_malzeme'].value_counts())
        print("\nİlk 10 Kayıt:")
        print(df.head(10))

    print(f"\n--- {plaka} Araç Bilgileri ---")
    arac_query = "SELECT * FROM araclar WHERE plaka = ?"
    arac_df = pd.read_sql_query(arac_query, conn, params=(plaka,))
    print(arac_df)

    conn.close()

if __name__ == "__main__":
    check_plate_data('46AKT453')

def explore_db():
    conn = sqlite3.connect('kargo_data.db')
    cursor = conn.cursor()
    
    # 1. Şemayı yazdır
    print("-" * 50)
    print("YAKIT Tablosu Şeması:")
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='yakit'")
    print(cursor.fetchone()[0])
    
    # 2. Örnek veri (İlk 5 kayıt)
    print("\n" + "-" * 50)
    print("Örnek Kayıtlar (İlk 5):")
    cursor.execute("SELECT * FROM yakit LIMIT 5")
    columns = [description[0] for description in cursor.description]
    print(columns)
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    explore_db()
