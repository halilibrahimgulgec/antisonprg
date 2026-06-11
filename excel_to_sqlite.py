import pandas as pd
import os
import glob
import hashlib
import sqlite3
from datetime import datetime


# Klasör yolu
klasor = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(klasor, 'kargo_data.db')

def check_and_fix_db():
    # Veritabanı bozuksa sil
    if os.path.exists(db_path):
        try:
            test_conn = sqlite3.connect(db_path)
            test_conn.execute('SELECT 1')
            test_conn.close()
        except sqlite3.DatabaseError as e:
            print(f"[WARNING]  Veritabani bozuk, yeniden olusturuluyor...")
            try:
                test_conn.close()
            except:
                pass
            try:
                os.remove(db_path)
            except PermissionError:
                print(f"[ERROR] Veritabani dosyasi kullanimda!")
                print(f"   Cozum: Flask'i kapatin (CTRL+C) ve tekrar deneyin")
                # exit(1) # Asla server'ı kapatma!
                raise RuntimeError("Veritabani dosyasi kullanimda ve silinemiyor.")

# SQLite bağlantısı - Global bağlantıyı kaldırıyoruz
# conn = sqlite3.connect(db_path)
# cursor = conn.cursor()


# Tabloları oluştur
def create_tables(cursor, conn):
    """SQLite tablolarını oluştur"""

    # Yakit tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS yakit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plaka TEXT,
        islem_tarihi TEXT,
        saat TEXT,
        yakit_miktari REAL,
        birim_fiyat REAL,
        satir_tutari REAL,
        stok_adi TEXT,
        km_bilgisi REAL,
        km_fark REAL,
        litre_km REAL,
        toplam_yuk REAL,
        ton_litre REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Agirlik tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agirlik (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT,
        miktar REAL,
        birim TEXT,
        net_agirlik REAL,
        plaka TEXT,
        adres TEXT,
        islem_noktasi TEXT,
        cari_adi TEXT,
        ana_malzeme TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Arac takip tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS arac_takip (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plaka TEXT,
        sofor_adi TEXT,
        arac_gruplari TEXT,
        tarih TEXT,
        hareket_baslangic_tarihi TEXT,
        hareket_bitis_tarihi TEXT,
        baslangic_adresi TEXT,
        bitis_adresi TEXT,
        baslangic_koordinatlari TEXT,
        bitis_koordinatlari TEXT,
        baslangic_kilometre REAL,
        bitis_kilometre REAL,
        maksimum_hiz REAL,
        toplam_kilometre REAL,
        hareket_suresi TEXT,
        rolanti_suresi TEXT,
        park_suresi TEXT,
        toplam_asiri_hiz_alarmi INTEGER,
        toplam_rolanti_alarmi INTEGER,
        gunluk_yakit_tuketimi_l REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # İşlenmiş dosyalar tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        file_size INTEGER,
        file_hash TEXT,
        record_count INTEGER,
        table_name TEXT,
        processed_at TEXT,
        status TEXT,
        error_message TEXT
    )
    ''')

    conn.commit()
    print("[OK] SQLite tablolari olusturuldu: kargo_data.db\n")


def clear_failed_records(cursor, conn):
    """Hatalı işlenmiş dosya kayıtlarını temizle"""
    try:
        cursor.execute("DELETE FROM processed_files WHERE status = 'error'")
        count = cursor.rowcount
        conn.commit()
        if count > 0:
            print(f"[CLEAN] {count} hatali kayit temizlendi.\n")
        return count
    except Exception as e:
        print(f"[WARNING] Temizleme hatasi: {e}")
        return 0


def get_file_hash(file_path):
    """Dosyanın MD5 hash değerini hesapla"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_file_processed(cursor, filename, file_hash):
    """Dosya daha önce işlendi mi kontrol et"""
    try:
        cursor.execute("SELECT file_hash FROM processed_files WHERE filename = ?", (filename,))
        result = cursor.fetchone()

        if result:
            stored_hash = result[0]
            if stored_hash == file_hash:
                return True, "Aynı dosya daha önce işlendi"
            else:
                return False, "Dosya güncellendi, tekrar işlenecek"
        return False, "Yeni dosya"
    except Exception as e:
        print(f"[WARNING] Dosya kontrolu hatasi: {e}")
        return False, "Kontrol hatasi"


def mark_file_as_processed(cursor, conn, filename, file_size, file_hash, record_count, table_name, status="success", error_message=None):
    """Dosyayı işlenmiş olarak işaretle"""
    try:
        processed_at = datetime.now().isoformat()

        # Önce varsa sil
        cursor.execute("DELETE FROM processed_files WHERE filename = ?", (filename,))

        # Yeni ekle
        cursor.execute('''
            INSERT INTO processed_files
            (filename, file_size, file_hash, record_count, table_name, processed_at, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, file_size, file_hash, record_count, table_name, processed_at, status, error_message))

        conn.commit()
        return True
    except Exception as e:
        print(f"[WARNING] Dosya kayit hatasi: {e}")
        return False


def clean_column_name(col_name):
    """Sütun isimlerini temizle"""
    if pd.isna(col_name):
        return "unknown"
    col_name = str(col_name).strip()
    col_name = col_name.replace('\n', ' ').replace('\r', ' ')

    # Türkçe karakterleri dönüştür
    tr_map = {
        'ı': 'i', 'İ': 'i', 'ğ': 'g', 'Ğ': 'g',
        'ü': 'u', 'Ü': 'u', 'ş': 's', 'Ş': 's',
        'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    for tr_char, en_char in tr_map.items():
        col_name = col_name.replace(tr_char, en_char)

    col_name = ''.join(c for c in col_name if c.isalnum() or c.isspace() or c == '_')
    return col_name.lower().replace(' ', '_')

def normalize_and_align_columns(cols):
    """
    Sütun isimlerindeki tutarsızlıkları gidermek için akıllı eşleştirme algoritması.
    Örn: 'mazot', 'benzin', 'litre' -> 'yakit_miktari'
          'son_km', 'odometre' -> 'km_bilgisi'
    """
    aligned = {}
    
    # Eşleştirme Sözlüğü (Synonym Maps)
    synonym_map = {
        'plaka': ['plaka', 'plate', 'arac', 'vehicle', 'plaka_no'],
        'islem_tarihi': ['islem_tarihi', 'tarih', 'date', 'islem_tarih', 'tarihi'],
        'saat': ['saat', 'islem_saat', 'time', 'saati'],
        'yakit_miktari': ['yakit_miktari', 'yakit', 'mazot', 'benzin', 'motorin', 'diesel', 'fuel', 'litre', 'miktar', 'alinan_yakit', 'yakit_litre'],
        'km_bilgisi': ['km_bilgisi', 'son_km', 'odometre', 'odometer', 'km', 'kilometre', 'arac_km', 'end_km'],
        'km_fark': ['km_fark', 'yapilan_yol', 'fark_km', 'yol_km', 'yol', 'km_farki'],
        'litre_km': ['litre_km', 'litre_basina_km', 'tuketim_orani'],
        'toplam_yuk': ['toplam_yuk', 'yuk', 'weight', 'tonaj'],
        'ton_litre': ['ton_litre', 'verimlilik'],
        'birim_fiyat': ['birim_fiyat', 'fiyat', 'price'],
        'satir_tutari': ['satir_tutari', 'tutar', 'amount', 'toplam_tutar', 'maliyet'],
        'stok_adi': ['stok_adi', 'yakit_tipi', 'yakit_turu', 'yakit_cinsi', 'urun_adi', 'malzeme', 'stok', 'urun'],
        'cari_adi': ['cari_adi', 'cari_unvan', 'cari_adi_unvani', 'musteri', 'customer', 'cari', 'cari_unvani']
    }

    # Her girdi sütunu için en uygun anahtarı eşleştir
    for col in cols:
        matched = False
        for target_col, synonyms in synonym_map.items():
            if col == target_col or col in synonyms:
                aligned[col] = target_col
                matched = True
                break
        if not matched:
            # Kısmi eşleşme kontrolü (örn: içinde 'plak' geçiyor mu?)
            for target_col, synonyms in synonym_map.items():
                if any(syn in col for syn in synonyms):
                    aligned[col] = target_col
                    matched = True
                    break
            if not matched:
                aligned[col] = col # Eşleşmiyorsa orijinal ismi koru
                
    return aligned

def normalize_fuel_type(val):
    """
    Veritabanına eklenen yakıt türlerini anlamlandırıp normalize eder.
    Örn: 'motorin', 'mazot', 'diesel' -> 'MOTORİN'
          'benzin', 'gasoline', '95_oktan' -> 'BENZİN'
    """
    if pd.isna(val) or not val:
        return 'YAKIT'
    
    val_clean = str(val).strip().lower()
    
    motorin_synonyms = ['motorin', 'mazot', 'diesel', 'dizel', 'euro_diesel', 'eurodizel', 'fuel_oil', 'lpg']
    benzin_synonyms = ['benzin', 'gasoline', 'petrol', '95_oktan', '97_oktan']
    
    if any(syn in val_clean for syn in motorin_synonyms):
        return 'MOTORİN'
    elif any(syn in val_clean for syn in benzin_synonyms):
        return 'BENZİN'
        
    return 'YAKIT'

def auto_alter_table_if_needed(conn, table_name, df):
    """
    Eğer DataFrame'de veritabanında olmayan yeni sütunlar varsa,
    SQLite tablosunu dinamik olarak alter ederek yeni sütunları ekler.
    """
    try:
        cursor = conn.cursor()
        # Mevcut sütunları al
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        for col in df.columns:
            if col not in existing_cols and col != 'unknown':
                # Sütun türünü belirle (basitçe sayısal mı metinsel mi)
                col_type = "REAL" if pd.api.types.is_numeric_dtype(df[col]) else "TEXT"
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}"
                cursor.execute(alter_query)
                print(f"[SCHEMA] '{table_name}' tablosuna yeni sütun eklendi: {col} ({col_type})")
        conn.commit()
    except Exception as e:
        print(f"[SCHEMA ERROR] Tablo alter edilirken hata: {e}")


def insert_to_sqlite(conn, table_name, data_list):
    """SQLite'a toplu veri ekle"""
    if not data_list:
        return 0

    try:
        # DataFrame'e çevir
        df = pd.DataFrame(data_list)

        # SQLite'a yaz (append mode)
        df.to_sql(table_name, conn, if_exists='append', index=False)

        return len(data_list)
    except Exception as e:
        print(f"[ERROR] SQLite insert hatasi ({table_name}): {e}")
        raise



def process_excel_files(custom_directory=None):
    """
    Belirtilen klasördeki (veya varsayılan) Excel dosyalarını işler.
    custom_directory: Eğer None ise scriptin olduğu klasöre bakar.
    """
    target_dir = custom_directory if custom_directory else klasor
    
    print(f"[INFO] Islenecek klasor: {target_dir}")
    
    # Veritabanı bağlantısı (fonksiyon içinde yeniden açılmalı)
    local_conn = sqlite3.connect(db_path)
    local_cursor = local_conn.cursor()
    
    # Tabloları oluştur (emin olmak için)
    create_tables(local_cursor, local_conn)
    
    # Hatalı kayıtları temizle
    clear_failed_records(local_cursor, local_conn)
    
    
    # Excel/CSV dosyalarını al
    dosyalar_xlsx = [f for f in glob.glob(os.path.join(target_dir, "*.xlsx")) if not os.path.basename(f).startswith('~$')]
    dosyalar_xls = [f for f in glob.glob(os.path.join(target_dir, "*.xls")) if not os.path.basename(f).startswith('~$')]
    dosyalar_csv = [f for f in glob.glob(os.path.join(target_dir, "*.csv")) if not os.path.basename(f).startswith('~$')]
    dosyalar = dosyalar_xlsx + dosyalar_xls + dosyalar_csv
    
    islenen_say = 0
    atlanan_say = 0
    hatali_say = 0
    results = []

    print(f"[INFO] Toplam {len(dosyalar)} dosya bulundu (.xlsx, .xls, .csv)\n")

    for dosya in dosyalar:
        dosya_adi = os.path.basename(dosya)
        dosya_boyutu = os.path.getsize(dosya)
        dosya_hash = get_file_hash(dosya)

        # Dosya daha önce işlendi mi kontrol et
        is_processed, message = is_file_processed(local_cursor, dosya_adi, dosya_hash)

        if is_processed:
            print(f"[SKIP]  '{dosya_adi}' atlandi -> {message}")
            results.append({'filename': dosya_adi, 'status': 'skipped', 'message': message})
            atlanan_say += 1
            continue

        print(f"[PROCESSING] '{dosya_adi}' isleniyor...")
        
        try:
            df = None
            # Dosya okuma (yukarıdaki mantığın aynısı)
            if dosya.endswith('.csv'):
                encodings = ['utf-8', 'latin1', 'iso-8859-9', 'cp1254']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(dosya, encoding=encoding)
                        break
                    except:
                        continue
                if df is None:
                    df = pd.read_csv(dosya, encoding='utf-8', errors='ignore')
            elif dosya.endswith(('.xlsx', '.xls')):
                try:
                    temp_all = pd.read_excel(dosya, header=None)
                    found_header = False
                    for idx in range(min(10, len(temp_all))):
                        row = temp_all.iloc[idx].astype(str).str.lower()
                        if any(keyword in row.values for keyword in ['plaka', 'plate', 'tarih', 'date', 'miktar']):
                            df = pd.read_excel(dosya, skiprows=idx)
                            found_header = True
                            break
                    if not found_header:
                        df = pd.read_excel(dosya)
                except Exception as e:
                    print(f"Dosya okuma hatasi: {e}")
                    df = None

            if df is None or df.empty:
                mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, 0, None, "error", "Dosya bos veya okunamadi")
                print(f"[ERROR] '{dosya_adi}' -> Veri yok.")
                results.append({'filename': dosya_adi, 'status': 'error', 'message': 'Dosya bos veya okunamadi'})
                hatali_say += 1
                continue

            # Sütun temizleme ve akıllı hizalama/eşleştirme
            cols_clean = [clean_column_name(col) for col in df.columns]
            
            # Akıllı eşleme sözlüğünü uygula
            alignment_mapping = normalize_and_align_columns(cols_clean)
            
            # DataFrame sütunlarını normalize edilmiş isimlerle güncelle
            df.rename(columns=alignment_mapping, inplace=True)
            cols = df.columns.tolist()

            # Toplam satırı temizleme
            plate_cols = [c for c in cols if 'plaka' in c or 'plate' in c]
            if plate_cols:
                plaka_col = plate_cols[0]
                if plaka_col in df.columns:
                    df = df[df[plaka_col].notna()]
                    df = df[~df[plaka_col].astype(str).str.contains('toplam|total', case=False, na=True)]

            inserted = 0
            table_type = ""

            # --- YAKIT ---
            if 'plaka' in cols and ('yakit_miktari' in cols or 'km_bilgisi' in cols or 'km_fark' in cols):
                table_type = 'yakit'
                db_fields = ['plaka', 'islem_tarihi', 'saat', 'yakit_miktari', 'km_bilgisi', 'km_fark', 'litre_km', 'toplam_yuk', 'ton_litre', 'birim_fiyat', 'satir_tutari', 'stok_adi']
                
                # Eşleşenleri seç
                selected = [c for c in db_fields if c in cols]
                df_sel = df[selected].copy()
                
                # Yakıt türü normalizasyonu
                if 'stok_adi' in df_sel.columns:
                    df_sel['stok_adi'] = df_sel['stok_adi'].apply(normalize_fuel_type)
                else:
                    df_sel['stok_adi'] = 'MOTORİN' # Varsayılan yakıt türü
                    
                # Sayısal alanları dönüştür
                for col in ['yakit_miktari', 'km_bilgisi', 'km_fark', 'litre_km', 'toplam_yuk', 'ton_litre', 'birim_fiyat', 'satir_tutari']:
                    if col in df_sel.columns:
                        df_sel[col] = pd.to_numeric(df_sel[col], errors='coerce')
                
                # Tarih alanını dönüştür
                if 'islem_tarihi' in df_sel.columns:
                    df_sel['islem_tarihi'] = pd.to_datetime(df_sel['islem_tarihi'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Olmayan alanları None olarak ekle
                for col in db_fields:
                    if col not in df_sel.columns:
                        df_sel[col] = None

                # Veritabanında olmayan dinamik sütunlar varsa (Şema Genişletme)
                extra_cols = [c for c in cols if c not in db_fields and c != 'unknown' and c not in ['islem_tarihi', 'saat', 'yakit_miktari', 'km_bilgisi', 'km_fark', 'litre_km', 'toplam_yuk', 'ton_litre', 'birim_fiyat', 'satir_tutari', 'stok_adi', 'plaka']]
                if extra_cols:
                    for col in extra_cols:
                        df_sel[col] = df[col]
                    auto_alter_table_if_needed(local_conn, 'yakit', df_sel)

                records = df_sel.replace([float('nan'), float('inf'), float('-inf')], None).to_dict('records')
                if records:
                    inserted = insert_to_sqlite(local_conn, 'yakit', records)
                    mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, inserted, 'yakit')
                    print(f"[FUEL] '{dosya_adi}' -> {inserted} kayit 'yakit' tablosuna eklendi.")
                    islenen_say += 1

            # --- AGIRLIK ---
            elif ('net_agirlik' in cols or 'plaka' in cols) and ('miktar' in cols or 'birim' in cols):
                table_type = 'agirlik'
                db_fields = ['tarih', 'miktar', 'birim', 'net_agirlik', 'plaka', 'adres', 'islem_noktasi', 'cari_adi']
                selected = [c for c in db_fields if c in cols]
                df_sel = df[selected].copy()
                
                for col in ['miktar', 'net_agirlik']:
                    if col in df_sel.columns:
                        df_sel[col] = pd.to_numeric(df_sel[col], errors='coerce')
                
                if 'tarih' in df_sel.columns:
                    df_sel['tarih'] = pd.to_datetime(df_sel['tarih'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                
                if 'birim' in df_sel.columns:
                    df_sel['ana_malzeme'] = df_sel['birim'].apply(lambda x: 'KUM' if str(x).upper()=='KG' else 'BETON' if str(x).upper()=='M3' else 'PARKE' if str(x).upper()=='M2' else 'BORDRO' if str(x).upper()=='MT' else 'PALET' if str(x).upper()=='ADET' else str(x) if pd.notna(x) else None)
                else:
                    df_sel['ana_malzeme'] = None
                
                db_fields.append('ana_malzeme')
                for col in db_fields:
                    if col not in df_sel.columns:
                        df_sel[col] = None

                # Veritabanında olmayan dinamik sütunlar varsa (Şema Genişletme)
                extra_cols = [c for c in cols if c not in db_fields and c != 'unknown' and c not in ['tarih', 'miktar', 'birim', 'net_agirlik', 'plaka', 'adres', 'islem_noktasi', 'cari_adi', 'ana_malzeme']]
                if extra_cols:
                    for col in extra_cols:
                        df_sel[col] = df[col]
                    auto_alter_table_if_needed(local_conn, 'agirlik', df_sel)
                
                records = df_sel.replace([float('nan'), float('inf'), float('-inf')], None).to_dict('records')
                if records:
                    inserted = insert_to_sqlite(local_conn, 'agirlik', records)
                    mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, inserted, 'agirlik')
                    print(f"[WEIGHT]  '{dosya_adi}' -> {inserted} kayit 'agirlik' tablosuna eklendi.")
                    islenen_say += 1

            # --- ARAC TAKIP ---
            elif any(k.lower() in ['plaka', 'plate'] for k in cols) and any(k.lower() in ['toplam kilometre', 'sum_distance', 'toplam_kilometre'] for k in cols):
                table_type = 'arac_takip'
                mapping_raw = {
                    'plaka': 'plaka', 'plate': 'plaka', 'sofor_adi': 'sofor_adi', 'arac_gruplari': 'arac_gruplari',
                    'tarih': 'tarih', 'date': 'tarih', 'hareket_baslangic_tarihi': 'hareket_baslangic_tarihi',
                    'hareket_bitis_tarihi': 'hareket_bitis_tarihi', 'baslangic_adresi': 'baslangic_adresi',
                    'bitis_adresi': 'bitis_adresi', 'baslangic_koordinatlari': 'baslangic_koordinatlari',
                    'bitis_koordinatlari': 'bitis_koordinatlari', 'baslangic_kilometre': 'baslangic_kilometre',
                    'bitis_kilometre': 'bitis_kilometre', 'maksimum_hiz': 'maksimum_hiz', 'toplam_kilometre': 'toplam_kilometre',
                    'hareket_suresi': 'hareket_suresi', 'rolanti_suresi': 'rolanti_suresi', 'park_suresi': 'park_suresi',
                    'toplam_rolanti_alarmi': 'toplam_rolanti_alarmi', 'toplam_asiri_hiz_alarmi': 'toplam_asiri_hiz_alarmi',
                    'gunluk_yakit_tuketimi_l': 'gunluk_yakit_tuketimi_l'
                }
                # ... mapping ...
                selected_cols = {}
                for orig_col in df.columns:
                     orig_clean = clean_column_name(orig_col)
                     for k, v in mapping_raw.items():
                         if orig_clean == k or orig_clean == clean_column_name(k):
                             selected_cols[orig_col] = v
                             break
                
                if len(selected_cols) < 3:
                    # mark error
                    mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, 0, None, "error", "Yetersiz sutun")
                    print(f"[ERROR] '{dosya_adi}' -> Az sutun eslesti.")
                    results.append({'filename': dosya_adi, 'status': 'error', 'message': 'Yetersiz sutun'})
                    hatali_say += 1
                    continue
                
                df_sel = df[list(selected_cols.keys())].copy()
                df_sel.rename(columns=selected_cols, inplace=True)
                
                # Numeric convert...
                num_cols = ['baslangic_kilometre', 'bitis_kilometre', 'maksimum_hiz', 'toplam_kilometre', 'toplam_asiri_hiz_alarmi', 'toplam_rolanti_alarmi', 'gunluk_yakit_tuketimi_l']
                for col in num_cols:
                    if col in df_sel.columns: df_sel[col] = pd.to_numeric(df_sel[col], errors='coerce')
                    # Int convert for alarms
                    if col in ['toplam_asiri_hiz_alarmi', 'toplam_rolanti_alarmi'] and col in df_sel.columns:
                         df_sel[col] = df_sel[col].fillna(0).astype('Int64')

                # Date convert...
                for t_col in ['tarih', 'hareket_baslangic_tarihi', 'hareket_bitis_tarihi']:
                    if t_col in df_sel.columns:
                         df_sel[t_col] = pd.to_datetime(df_sel[t_col], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Fill missing...
                all_cols = [
                    'plaka', 'sofor_adi', 'arac_gruplari', 'tarih', 'hareket_baslangic_tarihi',
                    'hareket_bitis_tarihi', 'baslangic_adresi', 'bitis_adresi', 'baslangic_koordinatlari',
                    'bitis_koordinatlari', 'baslangic_kilometre', 'bitis_kilometre', 'maksimum_hiz',
                    'toplam_kilometre', 'hareket_suresi', 'rolanti_suresi', 'park_suresi',
                    'toplam_asiri_hiz_alarmi', 'toplam_rolanti_alarmi', 'gunluk_yakit_tuketimi_l'
                ]
                for col in all_cols:
                    if col not in df_sel.columns: df_sel[col] = None
                
                records = df_sel.replace([float('nan'), float('inf'), float('-inf')], None).to_dict('records')
                if records:
                    inserted = insert_to_sqlite(local_conn, 'arac_takip', records)
                    mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, inserted, 'arac_takip')
                    print(f"[TRACK] '{dosya_adi}' -> {inserted} kayit 'arac_takip' tablosuna eklendi.")
                    islenen_say += 1
            
            else:
                # mark error (unknown type)
                mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, 0, None, "error", "Bilinmeyen format")
                print(f"[UNKNOWN] '{dosya_adi}' -> Taninamadi.")
                results.append({'filename': dosya_adi, 'status': 'error', 'message': 'Format taninamadi'})
                hatali_say += 1

        except Exception as e:
            # mark error
            mark_file_as_processed(local_cursor, local_conn, dosya_adi, dosya_boyutu, dosya_hash, 0, None, "error", str(e))
            print(f"[ERROR] '{dosya_adi}' islenemedi: {e}")
            results.append({'filename': dosya_adi, 'status': 'error', 'message': str(e)})
            hatali_say += 1

    # Final logic: Plakaları güncelle
    try:
        local_cursor.execute('''
            INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, aktif, notlar)
            SELECT DISTINCT plaka, 'BIZIM', 'KARGO ARACI', 1, 'Otomatik eklendi'
            FROM yakit WHERE plaka IS NOT NULL
        ''')
        local_cursor.execute('''
            INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, aktif, notlar)
            SELECT DISTINCT plaka, 'BIZIM', 'KARGO ARACI', 1, 'Otomatik eklendi'
            FROM agirlik WHERE plaka IS NOT NULL
        ''')
        local_cursor.execute('''
            INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, aktif, notlar)
            SELECT DISTINCT plaka, 'BIZIM', 'KARGO ARACI', 1, 'Otomatik eklendi'
            FROM arac_takip WHERE plaka IS NOT NULL
        ''')
        local_conn.commit()
    except Exception as e:
        print(f"Plaka update hatasi: {e}")

    local_conn.close()
    
    return {
        'total': len(dosyalar),
        'processed': islenen_say,
        'skipped': atlanan_say,
        'failed': hatali_say,
        'results': results
    }

if __name__ == "__main__":
    # Veritabanı kontrolü sadece script doğrudan çalışınca yapılmalı
    check_and_fix_db()

    # Kendi bağlantımızı oluşturuyoruz
    main_conn = sqlite3.connect(db_path)
    main_cursor = main_conn.cursor()

    # Tabloları oluştur
    create_tables(main_cursor, main_conn)
    
    # Hatalı kayıtları temizle
    clear_failed_records(main_cursor, main_conn)

    # Bağlantıyı kapat (process_excel_files kendi açacak)
    main_conn.close()
    
    # İşlemi başlat
    process_excel_files()
