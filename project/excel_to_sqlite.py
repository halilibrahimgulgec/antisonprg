import pandas as pd
import sqlite3
import os
import re
from database import get_connection

DB_PATH = os.path.join(os.path.dirname(__file__), 'kargo_data.db')


def clean_plaka(plaka):
    if pd.isna(plaka):
        return None
    plaka = str(plaka).strip().upper()
    plaka = re.sub(r'\s+', ' ', plaka)
    return plaka if plaka else None


def clean_float(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(str(val).replace(',', '.').strip())
    except:
        return 0.0


def clean_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).strftime('%Y-%m-%d')
    except:
        return str(val).strip()


def ensure_arac_exists_conn(cursor, plaka, seen_plakalar):
    if plaka not in seen_plakalar:
        cursor.execute("SELECT id FROM araclar WHERE plaka = ?", (plaka,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, aktif) VALUES (?, 'Bizim', 'Kargo', 1)",
                (plaka,)
            )
        seen_plakalar.add(plaka)


def import_yakit(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, header=0)
        else:
            df = pd.read_csv(filepath, encoding='utf-8-sig')

        df.columns = [str(c).strip().lower() for c in df.columns]

        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ['plaka', 'araç', 'arac']):
                col_map['plaka'] = col
            elif any(k in col_lower for k in ['tarih', 'date', 'islem']):
                if 'plaka' not in col_lower:
                    col_map['tarih'] = col
            elif any(k in col_lower for k in ['saat', 'zaman', 'time']):
                col_map['saat'] = col
            elif any(k in col_lower for k in ['miktar', 'litre', 'lt', 'yakit']):
                col_map['yakit'] = col
            elif any(k in col_lower for k in ['birim', 'fiyat', 'unit']):
                col_map['birim'] = col
            elif any(k in col_lower for k in ['tutar', 'toplam', 'total', 'satir']):
                col_map['tutar'] = col
            elif any(k in col_lower for k in ['stok', 'urun', 'ürün', 'malzeme']):
                col_map['stok'] = col
            elif any(k in col_lower for k in ['km', 'kilometre']):
                col_map['km'] = col

        conn = get_connection()
        cursor = conn.cursor()
        seen_plakalar = set()
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            plaka = clean_plaka(row.get(col_map.get('plaka', ''), None))
            if not plaka:
                skipped += 1
                continue

            yakit_miktari = clean_float(row.get(col_map.get('yakit', ''), 0))
            if yakit_miktari <= 0:
                skipped += 1
                continue

            islem_tarihi = clean_date(row.get(col_map.get('tarih', ''), None))
            saat = str(row.get(col_map.get('saat', ''), '')).strip()
            birim_fiyat = clean_float(row.get(col_map.get('birim', ''), 0))
            satir_tutari = clean_float(row.get(col_map.get('tutar', ''), 0))
            stok_adi = str(row.get(col_map.get('stok', ''), 'Motorin')).strip()
            km_bilgisi = clean_float(row.get(col_map.get('km', ''), 0))

            if satir_tutari <= 0 and birim_fiyat > 0:
                satir_tutari = yakit_miktari * birim_fiyat

            ensure_arac_exists_conn(cursor, plaka, seen_plakalar)

            cursor.execute('''
                INSERT INTO yakit (plaka, islem_tarihi, saat, yakit_miktari, birim_fiyat, satir_tutari, stok_adi, km_bilgisi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plaka, islem_tarihi, saat, yakit_miktari, birim_fiyat, satir_tutari, stok_adi, km_bilgisi))
            inserted += 1

        conn.commit()
        conn.close()
        return {'success': True, 'inserted': inserted, 'skipped': skipped}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def import_kantar(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, header=0)
        else:
            df = pd.read_csv(filepath, encoding='utf-8-sig')

        df.columns = [str(c).strip().lower() for c in df.columns]

        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ['plaka', 'araç', 'arac']):
                col_map['plaka'] = col
            elif any(k in col_lower for k in ['tarih', 'date']):
                col_map['tarih'] = col
            elif any(k in col_lower for k in ['net', 'agirlik', 'ağırlık', 'ton']):
                col_map['net'] = col
            elif any(k in col_lower for k in ['miktar', 'brut', 'gross']):
                col_map['miktar'] = col
            elif any(k in col_lower for k in ['cari', 'musteri', 'firma', 'müşteri']):
                col_map['cari'] = col

        conn = get_connection()
        cursor = conn.cursor()
        seen_plakalar = set()
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            plaka = clean_plaka(row.get(col_map.get('plaka', ''), None))
            if not plaka:
                skipped += 1
                continue

            net_agirlik = clean_float(row.get(col_map.get('net', ''), 0))
            if net_agirlik <= 0:
                skipped += 1
                continue

            tarih = clean_date(row.get(col_map.get('tarih', ''), None))
            miktar = clean_float(row.get(col_map.get('miktar', ''), 0))
            cari_adi = str(row.get(col_map.get('cari', ''), '')).strip()

            ensure_arac_exists_conn(cursor, plaka, seen_plakalar)

            cursor.execute('''
                INSERT INTO agirlik (plaka, tarih, miktar, net_agirlik, cari_adi)
                VALUES (?, ?, ?, ?, ?)
            ''', (plaka, tarih, miktar, net_agirlik, cari_adi))
            inserted += 1

        conn.commit()
        conn.close()
        return {'success': True, 'inserted': inserted, 'skipped': skipped}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def import_takip(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, header=0)
        else:
            df = pd.read_csv(filepath, encoding='utf-8-sig')

        df.columns = [str(c).strip().lower() for c in df.columns]

        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ['plaka', 'araç', 'arac']):
                col_map['plaka'] = col
            elif any(k in col_lower for k in ['tarih', 'date']):
                col_map['tarih'] = col
            elif any(k in col_lower for k in ['baslangic', 'başlangıç', 'ilk', 'start']):
                col_map['km_bas'] = col
            elif any(k in col_lower for k in ['bitis', 'bitiş', 'son', 'end']):
                col_map['km_bit'] = col
            elif any(k in col_lower for k in ['fark', 'mesafe', 'distance']):
                col_map['fark'] = col
            elif any(k in col_lower for k in ['sure', 'süre', 'duration']):
                col_map['sure'] = col
            elif any(k in col_lower for k in ['surucu', 'sürücü', 'driver']):
                col_map['surucu'] = col
            elif any(k in col_lower for k in ['guzergah', 'güzergah', 'rota', 'route']):
                col_map['guzergah'] = col

        conn = get_connection()
        cursor = conn.cursor()
        seen_plakalar = set()
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            plaka = clean_plaka(row.get(col_map.get('plaka', ''), None))
            if not plaka:
                skipped += 1
                continue

            tarih = clean_date(row.get(col_map.get('tarih', ''), None))
            km_bas = clean_float(row.get(col_map.get('km_bas', ''), 0))
            km_bit = clean_float(row.get(col_map.get('km_bit', ''), 0))
            fark = clean_float(row.get(col_map.get('fark', ''), 0))
            if fark <= 0 and km_bit > km_bas:
                fark = km_bit - km_bas
            sure = clean_float(row.get(col_map.get('sure', ''), 0))
            surucu = str(row.get(col_map.get('surucu', ''), '')).strip()
            guzergah = str(row.get(col_map.get('guzergah', ''), '')).strip()

            ensure_arac_exists_conn(cursor, plaka, seen_plakalar)

            cursor.execute('''
                INSERT INTO takip (plaka, tarih, km_baslangic, km_bitis, km_fark, sure_dakika, surucu, guzergah)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plaka, tarih, km_bas, km_bit, fark, sure, surucu, guzergah))
            inserted += 1

        conn.commit()
        conn.close()
        return {'success': True, 'inserted': inserted, 'skipped': skipped}

    except Exception as e:
        return {'success': False, 'error': str(e)}
