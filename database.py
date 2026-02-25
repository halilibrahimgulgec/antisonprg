import sqlite3
import os
from typing import List, Dict, Any

DATABASE_PATH = 'kargo_data.db'

def get_db_connection():
    """SQLite veritabanı bağlantısı oluştur"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """SQLite Row objesini dict'e çevir"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}

def get_yakit_data():
    """Sadece aktif araçların yakıt verilerini çek"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        if araclar_exists:
            cursor.execute('''
                SELECT y.* FROM yakit y
                LEFT JOIN araclar a ON y.plaka = a.plaka
                WHERE a.plaka IS NULL OR a.aktif = 1
            ''')
        else:
            cursor.execute('SELECT * FROM yakit')

        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Yakıt verisi çekilemedi: {e}")
        return []

def get_agirlik_data():
    """Sadece aktif araçların ağırlık (kantar) verilerini çek"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        if araclar_exists:
            cursor.execute('''
                SELECT ag.* FROM agirlik ag
                LEFT JOIN araclar a ON ag.plaka = a.plaka
                WHERE a.plaka IS NULL OR a.aktif = 1
            ''')
        else:
            cursor.execute('SELECT * FROM agirlik')

        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Ağırlık verisi çekilemedi: {e}")
        return []

def get_arac_takip_data():
    """Araç takip verilerini çek"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM arac_takip')
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Araç takip verisi çekilemedi: {e}")
        return []

def get_all_plakas():
    """Aktif araçların plakalarını getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        all_plakalar = set()

        cursor.execute('SELECT DISTINCT plaka FROM yakit WHERE plaka IS NOT NULL')
        for row in cursor.fetchall():
            all_plakalar.add(row['plaka'])

        cursor.execute('SELECT DISTINCT plaka FROM agirlik WHERE plaka IS NOT NULL')
        for row in cursor.fetchall():
            all_plakalar.add(row['plaka'])

        cursor.execute('SELECT DISTINCT plaka FROM arac_takip WHERE plaka IS NOT NULL')
        for row in cursor.fetchall():
            all_plakalar.add(row['plaka'])

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        if araclar_exists:
            cursor.execute('SELECT plaka FROM araclar WHERE aktif = 1')
            aktif_plakalar = set([row['plaka'] for row in cursor.fetchall()])

            if aktif_plakalar:
                all_plakalar = all_plakalar.intersection(aktif_plakalar)

        conn.close()
        return sorted(list(all_plakalar))
    except Exception as e:
        print(f"Plakalar getirilemedi: {e}")
        return []

def get_yakit_by_plaka(plaka):
    """Belirli bir plakaya ait yakıt verilerini getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM yakit WHERE plaka = ?', (plaka,))
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Plaka bazlı yakıt verisi çekilemedi: {e}")
        return []

def get_agirlik_by_plaka(plaka, sadece_urun=False):
    """Belirli bir plakaya ait ağırlık verilerini getir

    Args:
        plaka: Araç plakası
        sadece_urun: True ise sadece ürün kayıtlarını getir (Adet hariç)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if sadece_urun:
            cursor.execute('''
                SELECT * FROM agirlik
                WHERE plaka = ?
                AND birim NOT IN ('Adet', 'adet', 'ADET')
            ''', (plaka,))
        else:
            cursor.execute('SELECT * FROM agirlik WHERE plaka = ?', (plaka,))

        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Plaka bazlı ağırlık verisi çekilemedi: {e}")
        return []

def get_arac_takip_by_plaka(plaka):
    """Belirli bir plakaya ait araç takip verilerini getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM arac_takip WHERE plaka = ?', (plaka,))
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Plaka bazlı araç takip verisi çekilemedi: {e}")
        return []

def calc_real_distance(plaka, baslangic_tarihi=None, bitis_tarihi=None, limit=2000):
    """
    Araç bazlı gerçek gidilen mesafeyi (farkları toplayarak) hesapla.
    Kargo araçları için 'Kilometre', İş makineleri için 'Saat' değerini döner.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(km_fark) as toplam FROM yakit WHERE plaka = ? AND km_fark > 0 AND km_fark < ?"
        params = [plaka, limit]
        
        if baslangic_tarihi:
            query += " AND islem_tarihi >= ?"
            params.append(baslangic_tarihi)
        if bitis_tarihi:
            query += " AND islem_tarihi <= ?"
            params.append(bitis_tarihi)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        toplam_km = float(row['toplam'] or 0)
        
        # Fallback: km_fark verisi yoksa (eski kayıtlar) MAX-MIN hesapla ama makul bir limit koy
        if toplam_km == 0:
            fb_query = "SELECT MIN(km_bilgisi) as min_km, MAX(km_bilgisi) as max_km FROM yakit WHERE plaka = ?"
            fb_params = [plaka]
            if baslangic_tarihi:
                fb_query += " AND islem_tarihi >= ?"
                fb_params.append(baslangic_tarihi)
            if bitis_tarihi:
                fb_query += " AND islem_tarihi <= ?"
                fb_params.append(bitis_tarihi)
            
            cursor.execute(fb_query, fb_params)
            fb_row = cursor.fetchone()
            if fb_row and fb_row['max_km'] and fb_row['min_km']:
                diff = fb_row['max_km'] - fb_row['min_km']
                # Eğer fark mantıklıysa (örn: tek bir tarih aralığında 20.000 km'den azsa) kabul et
                if 0 < diff < 20000:
                    toplam_km = float(diff)
        
        conn.close()
        return toplam_km
    except Exception as e:
        print(f"Mesafe hesaplama hatası ({plaka}): {e}")
        return 0.0

def get_statistics(baslangic=None, bitis=None, plaka=None, dahil_taseron=False):
    """Genel istatistikleri hesapla - Filtreleme desteği eklendi"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Filtreleri hazırla
        where_clauses = []
        params = []
        
        if baslangic:
            where_clauses.append("islem_tarihi >= ?")
            params.append(baslangic)
        if bitis:
            where_clauses.append("islem_tarihi <= ?")
            params.append(bitis)
        if plaka:
            where_clauses.append("plaka = ?")
            params.append(plaka)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Yakıt kaydı sayısı
        cursor.execute(f'SELECT COUNT(*) as count FROM yakit{where_sql}', params)
        yakit_count = cursor.fetchone()['count']

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        # Ağırlık kaydı sayısı (Filtreli)
        agirlik_where = ['ag.birim NOT IN ("Adet", "adet", "ADET")']
        agirlik_params = []
        
        ag_join = " ag"
        if not dahil_taseron and araclar_exists:
            ag_join += " INNER JOIN araclar a ON ag.plaka = a.plaka"
            agirlik_where.append("a.sahip = 'BİZİM'")
            agirlik_where.append("a.aktif = 1")

        if baslangic:
            agirlik_where.append("ag.tarih >= ?")
            agirlik_params.append(baslangic)
        if bitis:
            agirlik_where.append("ag.tarih <= ?")
            agirlik_params.append(bitis)
        if plaka:
            agirlik_where.append("ag.plaka = ?")
            agirlik_params.append(plaka)

        ag_where_sql = " WHERE " + " AND ".join(agirlik_where)
        cursor.execute(f'SELECT COUNT(*) as count FROM agirlik{ag_join}{ag_where_sql}', agirlik_params)
        agirlik_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM arac_takip')
        arac_count = cursor.fetchone()['count']

        toplam_motorin = 0.0
        toplam_adblue = 0.0
        toplam_yakit = 0.0
        toplam_maliyet = 0.0
        toplam_kilometre = 0.0
        plaka_sayisi = 0
        plakalar = []

        if araclar_exists:
            query = '''
                SELECT y.yakit_miktari, y.satir_tutari, y.stok_adi
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                WHERE y.yakit_miktari IS NOT NULL
                AND y.yakit_miktari > 0
                AND a.aktif = 1
            '''
            
            query_params = []
            if not dahil_taseron:
                query += " AND a.sahip = 'BİZİM'"
            
            if baslangic:
                query += " AND y.islem_tarihi >= ?"
                query_params.append(baslangic)
            if bitis:
                query += " AND y.islem_tarihi <= ?"
                query_params.append(bitis)
            if plaka:
                query += " AND y.plaka = ?"
                query_params.append(plaka)

            cursor.execute(query, query_params)
            yakit_data = cursor.fetchall()

            for row in yakit_data:
                try:
                    yakit_val = row['yakit_miktari']
                    stok_adi = str(row['stok_adi'] or '').upper()
                    
                    if yakit_val is not None and str(yakit_val).strip() != '':
                        float_val = float(yakit_val)
                        toplam_yakit += float_val
                        if 'ADBLUE' in stok_adi:
                            toplam_adblue += float_val
                        else:
                            toplam_motorin += float_val
                except (ValueError, TypeError):
                    pass

                try:
                    tutar_val = row['satir_tutari']
                    if tutar_val is not None and str(tutar_val).strip() != '':
                        toplam_maliyet += float(tutar_val)
                except (ValueError, TypeError):
                    pass

            # KM Hesabı (Araç bazlı gerçek farkları topla - daha güvenilir)
            km_query = '''
                SELECT SUM(y.km_fark) as total_diff
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                WHERE y.km_fark > 0 AND y.km_fark < 2000
                AND a.aktif = 1
            '''
            km_params = []
            if not dahil_taseron:
                km_query += " AND a.sahip = 'BİZİM'"
            if baslangic:
                km_query += " AND y.islem_tarihi >= ?"
                km_params.append(baslangic)
            if bitis:
                km_query += " AND y.islem_tarihi <= ?"
                km_params.append(bitis)
            if plaka:
                km_query += " AND y.plaka = ?"
                km_params.append(plaka)
            
            cursor.execute(km_query, km_params)
            km_row = cursor.fetchone()
            toplam_kilometre = float(km_row['total_diff'] or 0)

            # Eğer km_fark verisi hiç yoksa (eski sistem) fallback olarak MAX-MIN'e dön ama plaka bazlı
            if toplam_kilometre == 0:
                fb_query = '''
                    SELECT (MAX(y.km_bilgisi) - MIN(y.km_bilgisi)) as diff
                    FROM yakit y
                    INNER JOIN araclar a ON y.plaka = a.plaka
                    WHERE y.km_bilgisi > 0 AND a.aktif = 1
                '''
                fb_params = []
                if not dahil_taseron: fb_query += " AND a.sahip = 'BİZİM'"
                if baslangic: fb_query += " AND y.islem_tarihi >= ?"; fb_params.append(baslangic)
                if bitis: fb_query += " AND y.islem_tarihi <= ?"; fb_params.append(bitis)
                if plaka: fb_query += " AND y.plaka = ?"; fb_params.append(plaka)
                
                fb_query += " GROUP BY y.plaka"
                cursor.execute(fb_query, fb_params)
                km_rows = cursor.fetchall()
                toplam_kilometre = sum(float(r['diff'] or 0) for r in km_rows if 0 < (r['diff'] or 0) < 20000)

            # Plaka sayısını ve listesini de filtrelere göre güncelle
            count_query = '''
                SELECT COUNT(DISTINCT y.plaka) as count
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                WHERE a.aktif = 1
            '''
            list_query = '''
                SELECT DISTINCT y.plaka 
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                WHERE a.aktif = 1
            '''
            
            filter_sql = ""
            filter_params = []
            if not dahil_taseron:
                filter_sql += " AND a.sahip = 'BİZİM'"
            if baslangic:
                filter_sql += " AND y.islem_tarihi >= ?"
                filter_params.append(baslangic)
            if bitis:
                filter_sql += " AND y.islem_tarihi <= ?"
                filter_params.append(bitis)
            if plaka:
                filter_sql += " AND y.plaka = ?"
                filter_params.append(plaka)

            cursor.execute(count_query + filter_sql, filter_params)
            plaka_sayisi = cursor.fetchone()['count']

            cursor.execute(list_query + filter_sql + " ORDER BY y.plaka", filter_params)
            plakalar = [row['plaka'] for row in cursor.fetchall()]
        else:
            query = 'SELECT yakit_miktari, satir_tutari, stok_adi FROM yakit WHERE yakit_miktari IS NOT NULL AND yakit_miktari > 0'
            query_params = []
            if baslangic:
                query += " AND islem_tarihi >= ?"
                query_params.append(baslangic)
            if bitis:
                query += " AND islem_tarihi <= ?"
                query_params.append(bitis)
            if plaka:
                query += " AND plaka = ?"
                query_params.append(plaka)

            cursor.execute(query, query_params)
            yakit_data = cursor.fetchall()

            for row in yakit_data:
                try:
                    yakit_val = row['yakit_miktari']
                    stok_adi = str(row['stok_adi'] or '').upper()
                    
                    if yakit_val is not None and str(yakit_val).strip() != '':
                        float_val = float(yakit_val)
                        toplam_yakit += float_val
                        if 'ADBLUE' in stok_adi:
                            toplam_adblue += float_val
                        else:
                            toplam_motorin += float_val
                except (ValueError, TypeError):
                    pass

                try:
                    tutar_val = row['satir_tutari']
                    if tutar_val is not None and str(tutar_val).strip() != '':
                        toplam_maliyet += float(tutar_val)
                except (ValueError, TypeError):
                    pass

            count_query = 'SELECT COUNT(DISTINCT plaka) as count FROM yakit'
            list_query = 'SELECT DISTINCT plaka FROM yakit'
            
            if where_clauses:
                cursor.execute(count_query + where_sql, params)
                plaka_sayisi = cursor.fetchone()['count']
                cursor.execute(list_query + where_sql + " ORDER BY plaka", params)
                plakalar = [row['plaka'] for row in cursor.fetchall()]
            else:
                cursor.execute(count_query)
                plaka_sayisi = cursor.fetchone()['count']
                cursor.execute(list_query + " ORDER BY plaka")
                plakalar = [row['plaka'] for row in cursor.fetchall()]

            # KM Hesabı (Araçlar tablosu yoksa)
            km_query = "SELECT (MAX(km_bilgisi) - MIN(km_bilgisi)) as diff FROM yakit WHERE km_bilgisi IS NOT NULL AND km_bilgisi > 0"
            km_params = []
            if baslangic:
                km_query += " AND islem_tarihi >= ?"
                km_params.append(baslangic)
            if bitis:
                km_query += " AND islem_tarihi <= ?"
                km_params.append(bitis)
            if plaka:
                km_query += " AND plaka = ?"
                km_params.append(plaka)
            
            km_query += " GROUP BY plaka"
            cursor.execute(km_query, km_params)
            km_rows = cursor.fetchall()
            toplam_kilometre = sum(float(row['diff'] or 0) for row in km_rows)

        conn.close()

        return {
            'toplam_kayit': yakit_count + agirlik_count + arac_count,
            'yakit_kayit': yakit_count,
            'agirlik_kayit': agirlik_count,
            'arac_takip_kayit': arac_count,
            'plaka_sayisi': plaka_sayisi,
            'toplam_yakit': toplam_yakit,
            'toplam_kilometre': toplam_kilometre,
            'toplam_motorin': toplam_motorin,
            'toplam_adblue': toplam_adblue,
            'toplam_maliyet': toplam_maliyet,
            'plakalar': plakalar
        }
    except Exception as e:
        print(f"İstatistikler hesaplanamadı: {e}")
        return {
            'toplam_kayit': 0,
            'yakit_kayit': 0,
            'agirlik_kayit': 0,
            'arac_takip_kayit': 0,
            'plaka_sayisi': 0,
            'toplam_yakit': 0,
            'toplam_kilometre': 0,
            'toplam_motorin': 0,
            'toplam_adblue': 0,
            'toplam_maliyet': 0,
            'plakalar': []
        }

def check_database_exists():
    """Veritabanı dosyasının varlığını kontrol et"""
    return os.path.exists(DATABASE_PATH)

def get_all_araclar():
    """Tüm araçları getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM araclar ORDER BY plaka')
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Araçlar getirilemedi: {e}")
        return []

def add_arac(plaka, sahip, arac_tipi, notlar='', varsayilan_malzeme=None):
    """Yeni araç ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO araclar (plaka, sahip, arac_tipi, notlar, aktif, varsayilan_malzeme)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (plaka.strip().upper(), sahip, arac_tipi, notlar, varsayilan_malzeme))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Araç başarıyla eklendi'}
    except sqlite3.IntegrityError:
        return {'status': 'error', 'message': 'Bu plaka zaten kayıtlı!'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def update_arac(plaka, sahip, arac_tipi, aktif, notlar='', varsayilan_malzeme=None):
    """Araç bilgilerini güncelle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE araclar
            SET sahip = ?, arac_tipi = ?, aktif = ?, notlar = ?, varsayilan_malzeme = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE plaka = ?
        ''', (sahip, arac_tipi, int(aktif), notlar, varsayilan_malzeme, plaka))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Araç güncellendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def delete_arac(plaka):
    """Araç sil"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM araclar WHERE plaka = ?', (plaka,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Araç silindi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def bulk_import_araclar():
    """Tüm plakaları toplu olarak araclar tablosuna ekle - HIZLI VERSİYON"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, notlar, aktif)
            SELECT DISTINCT plaka, 'BİZİM', 'KARGO ARACI', 'Otomatik eklendi', 1
            FROM yakit
            WHERE plaka IS NOT NULL AND plaka != ''
        ''')

        eklenen = cursor.rowcount

        cursor.execute('SELECT COUNT(*) FROM araclar')
        toplam = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        return {
            'status': 'success',
            'eklenen': eklenen,
            'toplam': toplam,
            'message': f'{eklenen} yeni plaka eklendi'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_aktif_kargo_araclari(dahil_taseron=False):
    """Sadece aktif kargo araçlarını getir

    Args:
        dahil_taseron: True ise taşeron araçlar da dahil edilir
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if dahil_taseron:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1 AND arac_tipi = 'KARGO ARACI'
            ''')
        else:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1
                AND arac_tipi = 'KARGO ARACI'
                AND sahip = 'BİZİM'
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [row['plaka'] for row in rows]
    except Exception as e:
        print(f"Aktif kargo araçları getirilemedi: {e}")
        return []

def get_aktif_binek_araclar(dahil_taseron=False):
    """Sadece aktif binek araçları getir

    Args:
        dahil_taseron: True ise taşeron araçlar da dahil edilir
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if dahil_taseron:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1 AND arac_tipi = 'BİNEK ARAÇ'
            ''')
        else:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1
                AND arac_tipi = 'BİNEK ARAÇ'
                AND sahip = 'BİZİM'
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [row['plaka'] for row in rows]
    except Exception as e:
        print(f"Aktif binek araçları getirilemedi: {e}")
        return []

def get_aktif_is_makineleri(dahil_taseron=False):
    """Sadece aktif iş makinelerini getir

    Args:
        dahil_taseron: True ise taşeron araçlar da dahil edilir
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if dahil_taseron:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1 AND arac_tipi = 'İŞ MAKİNESİ'
            ''')
        else:
            cursor.execute('''
                SELECT plaka FROM araclar
                WHERE aktif = 1
                AND arac_tipi = 'İŞ MAKİNESİ'
                AND sahip = 'BİZİM'
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [row['plaka'] for row in rows]
    except Exception as e:
        print(f"Aktif iş makineleri getirilemedi: {e}")
        return []

def plaka_filtre_uygula():
    """Analizlerde kullanılacak plaka filtresini döndür

    Returns:
        tuple: (WHERE clause, parameters tuple)
    """
    try:
        aktif_plakalar = get_aktif_kargo_araclari()
        if not aktif_plakalar:
            return "", ()

        placeholders = ','.join('?' * len(aktif_plakalar))
        where_clause = f"plaka IN ({placeholders})"
        return where_clause, tuple(aktif_plakalar)
    except:
        return "", ()

def get_muhasebe_data(baslangic_tarihi, bitis_tarihi, plaka=None):
    """Muhasebe verilerini hesapla"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Tarih filtresi oluştur
        if baslangic_tarihi and bitis_tarihi:
            tarih_filtre_yakit = "WHERE islem_tarihi BETWEEN ? AND ?"
            tarih_filtre_agirlik = "WHERE tarih BETWEEN ? AND ?"
            tarih_params = (baslangic_tarihi, bitis_tarihi)
        else:
            tarih_filtre_yakit = ""
            tarih_filtre_agirlik = ""
            tarih_params = ()

        # Plaka filtresi ekle - SADECE AKTİF KARGO ARAÇLARI
        if plaka:
            yakit_query = f'''
                SELECT y.plaka, SUM(y.satir_tutari) as toplam_gider
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                {tarih_filtre_yakit.replace('islem_tarihi', 'y.islem_tarihi')}
                {"AND" if tarih_filtre_yakit else "WHERE"} y.plaka = ?
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI'
                GROUP BY y.plaka
            '''
            agirlik_query = f'''
                SELECT ag.plaka, SUM(ag.net_agirlik * 0.5) as toplam_gelir, MAX(ag.ana_malzeme) as ana_malzeme
                FROM agirlik ag
                INNER JOIN araclar a ON ag.plaka = a.plaka
                {tarih_filtre_agirlik.replace('tarih', 'ag.tarih')}
                {"AND" if tarih_filtre_agirlik else "WHERE"} ag.plaka = ?
                AND ag.birim NOT IN ('Adet', 'adet', 'ADET')
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI'
                GROUP BY ag.plaka
            '''
            cursor.execute(yakit_query, tarih_params + (plaka,))
            yakit_rows = cursor.fetchall()
            cursor.execute(agirlik_query, tarih_params + (plaka,))
            agirlik_rows = cursor.fetchall()
        else:
            yakit_query = f'''
                SELECT y.plaka, SUM(y.satir_tutari) as toplam_gider
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                {tarih_filtre_yakit.replace('islem_tarihi', 'y.islem_tarihi')}
                {"WHERE" if not tarih_filtre_yakit else "AND"} a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI'
                GROUP BY y.plaka
            '''
            agirlik_query = f'''
                SELECT ag.plaka, SUM(ag.net_agirlik * 0.5) as toplam_gelir, MAX(ag.ana_malzeme) as ana_malzeme
                FROM agirlik ag
                INNER JOIN araclar a ON ag.plaka = a.plaka
                {tarih_filtre_agirlik.replace('tarih', 'ag.tarih')}
                {"WHERE" if not tarih_filtre_agirlik else "AND"} ag.birim NOT IN ('Adet', 'adet', 'ADET')
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI'
                GROUP BY ag.plaka
            '''
            cursor.execute(yakit_query, tarih_params)
            yakit_rows = cursor.fetchall()
            cursor.execute(agirlik_query, tarih_params)
            agirlik_rows = cursor.fetchall()

        conn.close()

        plaka_veriler = {}
        for row in yakit_rows:
            p = row['plaka']
            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['gider'] = float(row['toplam_gider'] or 0)

        for row in agirlik_rows:
            p = row['plaka']
            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['gelir'] = float(row['toplam_gelir'] or 0)
            plaka_veriler[p]['ana_malzeme'] = row['ana_malzeme'] or 'Bilinmiyor'

        toplam_gelir = sum(v['gelir'] for v in plaka_veriler.values())
        toplam_gider = sum(v['gider'] for v in plaka_veriler.values())
        net_kar = toplam_gelir - toplam_gider
        kar_marji = (net_kar / toplam_gelir * 100) if toplam_gelir > 0 else 0

        plaka_bazli = []
        for p, v in plaka_veriler.items():
            net = v['gelir'] - v['gider']
            marji = (net / v['gelir'] * 100) if v['gelir'] > 0 else 0
            plaka_bazli.append({
                'plaka': p,
                'gelir': v['gelir'],
                'gider': v['gider'],
                'net_kar': net,
                'kar_marji': marji,
                'ana_malzeme': v['ana_malzeme']
            })

        plaka_bazli.sort(key=lambda x: x['net_kar'], reverse=True)

        return {
            'status': 'success',
            'toplam_gelir': toplam_gelir,
            'toplam_gider': toplam_gider,
            'net_kar': net_kar,
            'kar_marji': kar_marji,
            'plaka_bazli': plaka_bazli
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def get_arac_performans_analizi(plaka, baslangic_tarihi=None, bitis_tarihi=None):
    """Araç performans analizi - yakıt/km oranı ve tonaj bilgisi"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Tarih filtresi
        if baslangic_tarihi and bitis_tarihi:
            tarih_filtre_yakit = "AND islem_tarihi BETWEEN ? AND ?"
            tarih_filtre_agirlik = "AND tarih BETWEEN ? AND ?"
            tarih_params = (baslangic_tarihi, bitis_tarihi)
        else:
            tarih_filtre_yakit = ""
            tarih_filtre_agirlik = ""
            tarih_params = ()

        # Yakıt ve KM bilgisi
        yakit_query = f'''
            SELECT
                SUM(yakit_miktari) as toplam_yakit,
                SUM(km_bilgisi) as toplam_km,
                COUNT(*) as sefer_sayisi,
                AVG(yakit_miktari) as ort_yakit_sefer,
                AVG(birim_fiyat) as ort_birim_fiyat,
                SUM(satir_tutari) as toplam_maliyet
            FROM yakit
            WHERE plaka = ? {tarih_filtre_yakit}
            AND yakit_miktari IS NOT NULL AND yakit_miktari > 0
        '''
        cursor.execute(yakit_query, (plaka,) + tarih_params)
        yakit_row = cursor.fetchone()

        # Tonaj bilgisi (ağırlık tablosundan) - SADECE ÜRÜN (Adet HARİÇ)
        agirlik_query = f'''
            SELECT
                SUM(net_agirlik) as toplam_tonaj,
                COUNT(*) as yuklenme_sayisi,
                AVG(net_agirlik) as ort_tonaj_yuklenme
            FROM agirlik
            WHERE plaka = ? {tarih_filtre_agirlik}
            AND net_agirlik IS NOT NULL AND net_agirlik > 0
            AND birim NOT IN ('Adet', 'adet', 'ADET')
        '''
        cursor.execute(agirlik_query, (plaka,) + tarih_params)
        agirlik_row = cursor.fetchone()

        conn.close()

        # Hesaplamalar
        toplam_yakit = float(yakit_row['toplam_yakit'] or 0)
        toplam_km = float(yakit_row['toplam_km'] or 0)
        sefer_sayisi = int(yakit_row['sefer_sayisi'] or 0)
        toplam_maliyet = float(yakit_row['toplam_maliyet'] or 0)
        ort_yakit_sefer = float(yakit_row['ort_yakit_sefer'] or 0)
        ort_birim_fiyat = float(yakit_row['ort_birim_fiyat'] or 0)

        toplam_tonaj = float(agirlik_row['toplam_tonaj'] or 0)
        yuklenme_sayisi = int(agirlik_row['yuklenme_sayisi'] or 0)
        ort_tonaj_yuklenme = float(agirlik_row['ort_tonaj_yuklenme'] or 0)

        # Yakıt/KM oranı
        yakit_km_orani = (toplam_yakit / toplam_km) if toplam_km > 0 else 0

        # KM başına maliyet
        km_basina_maliyet = (toplam_maliyet / toplam_km) if toplam_km > 0 else 0

        # Ton/Yakıt oranı (litre başına kaç ton taşındı - yüksek = verimli)
        toplam_tonaj_ton = toplam_tonaj / 1000  # kg'den ton'a çevir
        ton_basina_yakit = (toplam_tonaj_ton / toplam_yakit) if toplam_yakit > 0 else 0

        # Verimlilik skoru (düşük = iyi)
        verimlilik_skoru = yakit_km_orani * 100 if yakit_km_orani > 0 else 0

        return {
            'status': 'success',
            'plaka': plaka,
            'baslangic_tarihi': baslangic_tarihi or 'Başlangıç',
            'bitis_tarihi': bitis_tarihi or 'Bugün',
            'yakit': {
                'toplam_yakit': round(toplam_yakit, 2),
                'toplam_km': round(toplam_km, 2),
                'sefer_sayisi': sefer_sayisi,
                'ort_yakit_sefer': round(ort_yakit_sefer, 2),
                'ort_birim_fiyat': round(ort_birim_fiyat, 2),
                'toplam_maliyet': round(toplam_maliyet, 2)
            },
            'tonaj': {
                'toplam_tonaj': round(toplam_tonaj, 2),
                'yuklenme_sayisi': yuklenme_sayisi,
                'ort_tonaj_yuklenme': round(ort_tonaj_yuklenme, 2)
            },
            'performans': {
                'yakit_km_orani': round(yakit_km_orani, 3),
                'km_basina_maliyet': round(km_basina_maliyet, 2),
                'ton_basina_yakit': round(ton_basina_yakit, 2),
                'verimlilik_skoru': round(verimlilik_skoru, 2)
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def get_database_info():
    """Veritabanı hakkında bilgi al"""
    if not check_database_exists():
        return {
            'exists': False,
            'path': DATABASE_PATH,
            'message': 'Veritabanı dosyası bulunamadı. Lütfen önce Excel dosyalarını yükleyin.'
        }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]

        table_info = {}
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            count = cursor.fetchone()['count']
            table_info[table] = count

        conn.close()

        return {
            'exists': True,
            'path': DATABASE_PATH,
            'tables': table_info,
            'message': 'Veritabanı bağlantısı başarılı'
        }
    except Exception as e:
        return {
            'exists': False,
            'path': DATABASE_PATH,
            'error': str(e),
            'message': f'Veritabanı hatası: {str(e)}'
        }

def create_bakim_table():
    """Bakım tablosunu oluştur"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bakim (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plaka TEXT NOT NULL,
                bakim_tipi TEXT NOT NULL,
                yapilan_islem TEXT,
                tarih DATE NOT NULL,
                km INTEGER,
                maliyet REAL,
                bir_sonraki_bakim_km INTEGER,
                bir_sonraki_bakim_tarih DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Bakım tablosu kontrol edildi/oluşturuldu'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def upgrade_bakim_table():
    """Bakım tablosuna yeni sütunları ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mevcut sütunları kontrol et
        cursor.execute("PRAGMA table_info(bakim)")
        columns = [info['name'] for info in cursor.fetchall()]
        
        new_columns = {
            'bildiren_kisi': 'TEXT',
            'iletisim_tel': 'TEXT',
            'ariza_saati': 'TEXT',
            'ariza_konumu': 'TEXT',
            'operasyon_durumu': 'TEXT',
            'servis_adi': 'TEXT',
            'servis_giris_tarihi': 'DATE',
            'servis_cikis_tarihi': 'DATE',
            'iscilik_maliyeti': 'REAL',
            'parca_maliyeti': 'REAL',
            'fatura_no': 'TEXT',
            'garanti_durumu': 'TEXT'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Sütun ekleniyor: {col_name}")
                cursor.execute(f'ALTER TABLE bakim ADD COLUMN {col_name} {col_type}')
                
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Tablo yapısı güncellendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def add_bakim_kaydi(data):
    """Yeni bakım kaydı ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Maliyet hesaplama
        iscilik = float(data.get('iscilik_maliyeti') or 0)
        parca = float(data.get('parca_maliyeti') or 0)
        toplam_maliyet = float(data.get('maliyet') or (iscilik + parca))
        
        cursor.execute('''
            INSERT INTO bakim (
                plaka, bakim_tipi, yapilan_islem, tarih, km, maliyet, 
                bir_sonraki_bakim_km, bir_sonraki_bakim_tarih,
                bildiren_kisi, iletisim_tel, ariza_saati, ariza_konumu,
                operasyon_durumu, servis_adi, servis_giris_tarihi,
                servis_cikis_tarihi, iscilik_maliyeti, parca_maliyeti,
                fatura_no, garanti_durumu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('plaka'),
            data.get('bakim_tipi'),
            data.get('yapilan_islem'),
            data.get('tarih'),
            data.get('km'),
            toplam_maliyet,
            data.get('bir_sonraki_bakim_km'),
            data.get('bir_sonraki_bakim_tarih'),
            data.get('bildiren_kisi'),
            data.get('iletisim_tel'),
            data.get('ariza_saati'),
            data.get('ariza_konumu'),
            data.get('operasyon_durumu'),
            data.get('servis_adi'),
            data.get('servis_giris_tarihi'),
            data.get('servis_cikis_tarihi'),
            iscilik,
            parca,
            data.get('fatura_no'),
            data.get('garanti_durumu')
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Bakım kaydı başarıyla eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_bakim_kayitlari(plaka=None):
    """Bakım kayıtlarını getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if plaka:
            cursor.execute('SELECT * FROM bakim WHERE plaka = ? ORDER BY tarih DESC', (plaka,))
        else:
            cursor.execute('SELECT * FROM bakim ORDER BY tarih DESC')
            
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Bakım kayıtları getirilemedi: {e}")
        return []

def delete_bakim(bakim_id):
    """Bakım kaydını sil"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bakim WHERE id = ?', (bakim_id,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Bakım kaydı silindi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_bakim_analiz_data():
    """Bakım analizi için özet verileri getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Aylık Maliyetler (Son 6 ay)
        cursor.execute('''
            SELECT strftime('%Y-%m', tarih) as ay, SUM(maliyet) as toplam
            FROM bakim
            WHERE tarih >= date('now', '-6 months')
            GROUP BY ay
            ORDER BY ay
        ''')
        aylik_maliyetler = [{'ay': row['ay'], 'toplam': row['toplam']} for row in cursor.fetchall()]

        # 2. Arıza Türü Dağılımı
        cursor.execute('''
            SELECT bakim_tipi, COUNT(*) as adet
            FROM bakim
            GROUP BY bakim_tipi
        ''')
        ariza_dagilimi = [{'tip': row['bakim_tipi'], 'adet': row['adet']} for row in cursor.fetchall()]

        # 3. Araç Bazlı Maliyet (Top 10)
        cursor.execute('''
            SELECT plaka, SUM(maliyet) as toplam
            FROM bakim
            GROUP BY plaka
            ORDER BY toplam DESC
            LIMIT 10
        ''')
        arac_maliyetleri = [{'plaka': row['plaka'], 'toplam': row['toplam']} for row in cursor.fetchall()]

        # 4. KPI Özetleri
        # Bu ayki toplam
        cursor.execute('''
            SELECT SUM(maliyet) as bu_ay_toplam, COUNT(*) as bu_ay_adet
            FROM bakim
            WHERE strftime('%Y-%m', tarih) = strftime('%Y-%m', 'now')
        ''')
        bu_ay = cursor.fetchone()
        
        # Toplam harcama
        cursor.execute('SELECT SUM(maliyet) as genel_toplam FROM bakim')
        genel_toplam = cursor.fetchone()['genel_toplam'] or 0

        # Servisteki araçlar (çıkış tarihi boş veya gelecekte olanlar)
        cursor.execute('''
            SELECT COUNT(*) as serviste
            FROM bakim 
            WHERE servis_giris_tarihi IS NOT NULL 
            AND (servis_cikis_tarihi IS NULL OR servis_cikis_tarihi > date('now'))
        ''')
        serviste_sayisi = cursor.fetchone()['serviste']

        conn.close()

        return {
            'aylik_maliyetler': aylik_maliyetler,
            'ariza_dagilimi': ariza_dagilimi,
            'arac_maliyetleri': arac_maliyetleri,
            'kpi': {
                'bu_ay_toplam': bu_ay['bu_ay_toplam'] or 0,
                'bu_ay_adet': bu_ay['bu_ay_adet'] or 0,
                'genel_toplam': genel_toplam,
                'serviste_sayisi': serviste_sayisi
            }
        }
    except Exception as e:
        print(f"Analiz verisi hatası: {e}")
        return {
            'aylik_maliyetler': [],
            'ariza_dagilimi': [],
            'arac_maliyetleri': [],
            'kpi': {'bu_ay_toplam': 0, 'bu_ay_adet': 0, 'genel_toplam': 0, 'serviste_sayisi': 0}
        }
