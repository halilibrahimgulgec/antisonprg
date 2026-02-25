import sqlite3
import pandas as pd
from ai_model import PerformansAnalizi

def debug_performans():
    print("--- Performans Analizi Debug Başlatıldı ---")
    analiz = PerformansAnalizi()
    
    tipler = ['KARGO ARACI', 'İŞ MAKİNESİ', 'BİNEK ARAÇ']
    
    for tip in tipler:
        print(f"\nAnaliz Ediliyor: {tip}")
        try:
            result = analiz.plaka_performans_karsilastirma(arac_tipi_filtre=tip)
            
            if result['status'] == 'success':
                print(f"OK: {result['toplam_arac']} arac bulundu.")
                import json
                with open(f"debug_{tip.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            else:
                print(f"HATA: {result['message']}")
        except Exception as e:
            print(f"KRITIK HATA: {str(e)}")
            continue
            
            # Veri durumuna bakalım
            conn = sqlite3.connect('kargo_data.db')
            arac_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM araclar WHERE arac_tipi = '{tip}'", conn).iloc[0]['count']
            yakit_count = pd.read_sql_query(f"SELECT COUNT(DISTINCT plaka) as count FROM yakit WHERE plaka IN (SELECT plaka FROM araclar WHERE arac_tipi = '{tip}')", conn).iloc[0]['count']
            conn.close()
            
            print(f"   - Veritabanında Bu Tipte Kayıtlı Araç: {arac_count}")
            print(f"   - Yakıt Kaydı Olan Araç Sayısı: {yakit_count}")

            # Yakıt verilerine bakalım (km_fark > 0 kontrolü için)
            if analiz.yakit_data is not None and not analiz.yakit_data.empty:
                tip_data = analiz.yakit_data.merge(
                    pd.read_sql_query(f"SELECT plaka, arac_tipi FROM araclar WHERE arac_tipi = '{tip}'", sqlite3.connect('kargo_data.db')),
                    on='plaka'
                )
                print(f"   - Yakıt Verisindeki Toplam Satır: {len(tip_data)}")
                print(f"   - km_fark > 0 olan satır: {len(tip_data[tip_data['km_fark'] > 0])}")

if __name__ == "__main__":
    debug_performans()
