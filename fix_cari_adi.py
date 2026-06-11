import sqlite3
import pandas as pd
import glob
import os

db_path = 'kargo_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

files = glob.glob('*.xls') + glob.glob('*.xlsx')
print("Found files:", files)

total_updated = 0

for f in files:
    if any(k in f.lower() for k in ['yakit', 'motorin', 'report', 'deneme']):
        continue
    print(f"Processing {f}...")
    try:
        df = pd.read_excel(f)
        # Find header
        header_row = 0
        found = False
        for idx in range(min(10, len(df))):
            row_vals = df.iloc[idx].astype(str).str.lower().values
            if any(k in row_vals for k in ['plaka', 'plate', 'tarih', 'date', 'miktar']):
                df = pd.read_excel(f, skiprows=idx)
                found = True
                break
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find Cari Ünvan col
        cari_col = None
        for c in df.columns:
            if 'cari' in c.lower() or 'ünvan' in c.lower() or 'unvan' in c.lower():
                cari_col = c
                break
                
        if not cari_col:
            print(f"No cari column found in {f}")
            continue
            
        print(f"Cari column: {cari_col}")
        
        plaka_col = [c for c in df.columns if 'plaka' in c.lower() or 'plate' in c.lower()][0]
        miktar_col = [c for c in df.columns if 'miktar' in c.lower() or 'amount' in c.lower() or 'qty' in c.lower()][0]
        tarih_col = [c for c in df.columns if 'tarih' in c.lower() or 'date' in c.lower()][0]
        
        net_col = None
        for c in df.columns:
            if 'net' in c.lower() and ('ağırlık' in c.lower() or 'agirlik' in c.lower()):
                net_col = c
                break
                
        for idx, row in df.iterrows():
            plaka = str(row[plaka_col]).strip()
            miktar = pd.to_numeric(row[miktar_col], errors='coerce')
            tarih = pd.to_datetime(row[tarih_col], errors='coerce')
            cari = str(row[cari_col]).strip() if pd.notna(row[cari_col]) else None
            
            if pd.isna(miktar) or not plaka or plaka.lower() == 'nan':
                continue
                
            tarih_str_ymd = tarih.strftime('%Y-%m-%d') if pd.notna(tarih) else None
            
            if net_col:
                net_wt = pd.to_numeric(row[net_col], errors='coerce')
                if pd.notna(net_wt):
                    cursor.execute("""
                        UPDATE agirlik 
                        SET cari_adi = ? 
                        WHERE plaka = ? AND abs(miktar - ?) < 0.1 AND abs(net_agirlik - ?) < 0.1 AND tarih LIKE ?
                    """, (cari, plaka, float(miktar), float(net_wt), f"{tarih_str_ymd}%"))
                else:
                    cursor.execute("""
                        UPDATE agirlik 
                        SET cari_adi = ? 
                        WHERE plaka = ? AND abs(miktar - ?) < 0.1 AND tarih LIKE ?
                    """, (cari, plaka, float(miktar), f"{tarih_str_ymd}%"))
            else:
                cursor.execute("""
                    UPDATE agirlik 
                    SET cari_adi = ? 
                    WHERE plaka = ? AND abs(miktar - ?) < 0.1 AND tarih LIKE ?
                """, (cari, plaka, float(miktar), f"{tarih_str_ymd}%"))
                
            total_updated += cursor.rowcount
    except Exception as e:
        print(f"Error processing {f}: {e}")

conn.commit()
conn.close()
print(f"Finished updating. Total rows touched: {total_updated}")
