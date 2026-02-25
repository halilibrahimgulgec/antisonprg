"""
Excel dosyalarındaki sütun adlarını kontrol et
"""
import pandas as pd
import os

print('🔍 EXCEL SÜTUN KONTROLÜ\n')
print('=' * 80)

files = [
    '1beton satış.xls',
    '1kantar satış.xls',
    '1motorin.xls'
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f'\n❌ {file_path} bulunamadı!')
        continue

    print(f'\n📄 {file_path}')
    print('-' * 80)

    try:
        # İlk 15 satırı oku (başlık satırını bul)
        temp_all = pd.read_excel(file_path, header=None)

        found_header = False
        for idx in range(min(15, len(temp_all))):
            row = temp_all.iloc[idx].astype(str).str.lower()

            # Plaka, tarih, miktar gibi anahtar kelimeler var mı?
            if any(keyword in row.values for keyword in ['plaka', 'plate', 'tarih', 'date', 'miktar']):
                print(f'   ✅ Başlık satırı: {idx}\n')
                df = pd.read_excel(file_path, skiprows=idx)

                print(f'   Sütunlar ({len(df.columns)} adet):')
                for i, col in enumerate(df.columns, 1):
                    print(f'      {i:2d}. {col}')

                print(f'\n   İlk kayıt örneği:')
                if len(df) > 0:
                    first_row = df.iloc[0]
                    for col in df.columns:
                        val = first_row[col]
                        if pd.notna(val):
                            print(f'      {col}: {val}')

                found_header = True
                break

        if not found_header:
            print('   ❌ Başlık satırı bulunamadı!')
            print(f'   İlk 3 satır:')
            for idx in range(min(3, len(temp_all))):
                print(f'      Satır {idx}: {temp_all.iloc[idx].tolist()[:5]}')

    except Exception as e:
        print(f'   ❌ Hata: {e}')

print('\n' + '=' * 80)
print('\n💡 ÖNEMLİ: "Net Ağırlık" veya "Tonaj" gibi sütun var mı kontrol edin!')
print('=' * 80)
