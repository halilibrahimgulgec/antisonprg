import sqlite3
import os
from typing import List, Dict, Any
from werkzeug.security import check_password_hash

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

def get_user_by_username(username):
    """Kullanıcı adıyla kullanıcı bilgilerini getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row)
    except Exception as e:
        print(f"Kullanıcı bilgisi çekilemedi: {e}")
        return None

def verify_user(username, password):
    """Kullanıcı adı ve şifreyi doğrula"""
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        return user
    return None

def get_all_users():
    """Tüm kullanıcıları getirir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]
    except Exception as e:
        print(f"Kullanıcılar listesi çekilemedi: {e}")
        return []

def add_new_user(username, password, role='user'):
    """Yeni kullanıcı ekler"""
    from werkzeug.security import generate_password_hash
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                       (username, hashed_password, role))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Kullanıcı eklenemedi: {e}")
        return False

def delete_user(user_id):
    """Kullanıcıyı siler"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Kullanıcı silinemedi: {e}")
        return False

def get_yakit_data(harici_gizle=False):
    """Sadece aktif araçların yakıt verilerini çek"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        sahip_filtresi = "AND a.sahip IN ('BİZİM', 'BIZIM', 'BZM')" if harici_gizle else ""

        if araclar_exists:
            cursor.execute(f'''
                SELECT y.* FROM yakit y
                LEFT JOIN araclar a ON y.plaka = a.plaka
                WHERE (a.plaka IS NULL OR a.aktif = 1) {sahip_filtresi}
            ''')
        else:
            cursor.execute('SELECT * FROM yakit')

        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Yakıt verisi çekilemedi: {e}")
        return []

def get_agirlik_data(harici_gizle=False):
    """Sadece aktif araçların ağırlık (kantar) verilerini çek"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='araclar'")
        araclar_exists = cursor.fetchone() is not None

        sahip_filtresi = "AND a.sahip IN ('BİZİM', 'BIZIM', 'BZM')" if harici_gizle else ""

        if araclar_exists:
            cursor.execute(f'''
                SELECT ag.* FROM agirlik ag
                LEFT JOIN araclar a ON ag.plaka = a.plaka
                WHERE (a.plaka IS NULL OR a.aktif = 1) {sahip_filtresi}
            ''')
        else:
            cursor.execute('SELECT * FROM agirlik')

        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Ağırlık verisi çekilemedi: {e}")
        return []
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

def get_muhasebe_data(baslangic_tarihi, bitis_tarihi, plaka=None, settings=None):
    """Muhasebe verilerini hesapla - Detaylı ve aylık trend dahil"""
    if settings is None:
        settings = {}
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ayarları al
        harici_gizle = settings.get('harici_gizle', True) # Varsayılan olarak dış araçları gizle
        sahip_filtresi = "AND a.sahip IN ('BİZİM', 'BIZIM', 'BZM')" if harici_gizle else ""

        # Tarih filtresi oluştur
        if baslangic_tarihi and bitis_tarihi:
            tarih_filtre_yakit = "WHERE islem_tarihi BETWEEN ? AND ?"
            tarih_filtre_agirlik = "WHERE tarih BETWEEN ? AND ?"
            tarih_filtre_bakim = "WHERE tarih BETWEEN ? AND ?"
            tarih_params = (baslangic_tarihi, bitis_tarihi)
        else:
            tarih_filtre_yakit = ""
            tarih_filtre_agirlik = ""
            tarih_filtre_bakim = ""
            tarih_params = ()

        # Plaka filtresi ekle - SADECE AKTİF KARGO ARAÇLARI
        if plaka:
            yakit_query = f'''
                SELECT y.plaka, y.islem_tarihi, y.stok_adi, SUM(y.satir_tutari) as toplam_gider, SUM(y.yakit_miktari) as toplam_yakit_miktari
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                {tarih_filtre_yakit.replace('islem_tarihi', 'y.islem_tarihi')}
                {"AND" if tarih_filtre_yakit else "WHERE"} y.plaka = ?
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY y.plaka, y.islem_tarihi, y.stok_adi
            '''
            bakim_query = f'''
                SELECT b.plaka, b.tarih, SUM(b.maliyet) as toplam_bakim_gider
                FROM bakim b
                INNER JOIN araclar a ON b.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'b.tarih')}
                {"AND" if tarih_filtre_bakim else "WHERE"} b.plaka = ?
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY b.plaka, b.tarih
            '''
            agirlik_query = f'''
                SELECT ag.plaka, ag.tarih, SUM(CASE WHEN ag.birim IN ('Kg', 'kg', 'KG') THEN ag.miktar / 1000.0 ELSE ag.miktar END) as toplam_agirlik, MAX(ag.ana_malzeme) as ana_malzeme, ag.cari_adi
                FROM agirlik ag
                INNER JOIN araclar a ON ag.plaka = a.plaka
                {tarih_filtre_agirlik.replace('tarih', 'ag.tarih')}
                {"AND" if tarih_filtre_agirlik else "WHERE"} ag.plaka = ?
                AND ag.birim NOT IN ('Adet', 'adet', 'ADET')
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY ag.plaka, ag.tarih, ag.cari_adi
            '''
            ceza_query = f'''
                SELECT c.plaka, c.tarih, SUM(c.tutar) as toplam_ceza_gider
                FROM cezalar c
                INNER JOIN araclar a ON c.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'c.tarih')}
                {"AND" if tarih_filtre_bakim else "WHERE"} c.plaka = ?
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY c.plaka, c.tarih
            '''
            hasar_query = f'''
                SELECT h.plaka, h.tarih, SUM(h.tutar) as toplam_hasar_gider
                FROM hasarlar h
                INNER JOIN araclar a ON h.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'h.tarih')}
                {"AND" if tarih_filtre_bakim else "WHERE"} h.plaka = ?
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                AND h.sigorta_karsiladi_mi = 0
                GROUP BY h.plaka, h.tarih
            '''
            cursor.execute(yakit_query, tarih_params + (plaka,))
            yakit_rows = cursor.fetchall()
            cursor.execute(bakim_query, tarih_params + (plaka,))
            bakim_rows = cursor.fetchall()
            cursor.execute(agirlik_query, tarih_params + (plaka,))
            agirlik_rows = cursor.fetchall()
            cursor.execute(ceza_query, tarih_params + (plaka,))
            ceza_rows = cursor.fetchall()
            cursor.execute(hasar_query, tarih_params + (plaka,))
            hasar_rows = cursor.fetchall()
        else:
            yakit_query = f'''
                SELECT y.plaka, y.islem_tarihi, y.stok_adi, SUM(y.satir_tutari) as toplam_gider, SUM(y.yakit_miktari) as toplam_yakit_miktari
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                {tarih_filtre_yakit.replace('islem_tarihi', 'y.islem_tarihi')}
                {"WHERE" if not tarih_filtre_yakit else "AND"} a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY y.plaka, y.islem_tarihi, y.stok_adi
            '''
            bakim_query = f'''
                SELECT b.plaka, b.tarih, SUM(b.maliyet) as toplam_bakim_gider
                FROM bakim b
                INNER JOIN araclar a ON b.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'b.tarih')}
                {"WHERE" if not tarih_filtre_bakim else "AND"} a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY b.plaka, b.tarih
            '''
            agirlik_query = f'''
                SELECT ag.plaka, ag.tarih, SUM(CASE WHEN ag.birim IN ('Kg', 'kg', 'KG') THEN ag.miktar / 1000.0 ELSE ag.miktar END) as toplam_agirlik, MAX(ag.ana_malzeme) as ana_malzeme, ag.cari_adi
                FROM agirlik ag
                INNER JOIN araclar a ON ag.plaka = a.plaka
                {tarih_filtre_agirlik.replace('tarih', 'ag.tarih')}
                {"WHERE" if not tarih_filtre_agirlik else "AND"} ag.birim NOT IN ('Adet', 'adet', 'ADET')
                AND a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY ag.plaka, ag.tarih, ag.cari_adi
            '''
            ceza_query = f'''
                SELECT c.plaka, c.tarih, SUM(c.tutar) as toplam_ceza_gider
                FROM cezalar c
                INNER JOIN araclar a ON c.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'c.tarih')}
                {"WHERE" if not tarih_filtre_bakim else "AND"} a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                GROUP BY c.plaka, c.tarih
            '''
            hasar_query = f'''
                SELECT h.plaka, h.tarih, SUM(h.tutar) as toplam_hasar_gider
                FROM hasarlar h
                INNER JOIN araclar a ON h.plaka = a.plaka
                {tarih_filtre_bakim.replace('tarih', 'h.tarih')}
                {"WHERE" if not tarih_filtre_bakim else "AND"} a.aktif = 1 AND a.arac_tipi = 'KARGO ARACI' {sahip_filtresi}
                AND h.sigorta_karsiladi_mi = 0
                GROUP BY h.plaka, h.tarih
            '''
            cursor.execute(yakit_query, tarih_params)
            yakit_rows = cursor.fetchall()
            cursor.execute(bakim_query, tarih_params)
            bakim_rows = cursor.fetchall()
            cursor.execute(agirlik_query, tarih_params)
            agirlik_rows = cursor.fetchall()
            cursor.execute(ceza_query, tarih_params)
            ceza_rows = cursor.fetchall()
            cursor.execute(hasar_query, tarih_params)
            hasar_rows = cursor.fetchall()

        conn.close()

        def extract_month(tarih_str):
            if not tarih_str: return 'Bilinmiyor'
            try:
                if '-' in tarih_str:
                    parts = tarih_str.split(' ')[0].split('-')
                    if len(parts) >= 2: return f"{parts[0]}-{parts[1]}"
                elif '.' in tarih_str:
                    parts = tarih_str.split(' ')[0].split('.')
                    if len(parts) >= 3: return f"{parts[2]}-{parts[1]}"
            except:
                pass
            return 'Bilinmiyor'

        plaka_veriler = {}
        aylik_veriler = {}
        cari_veriler = {}
        
        motorin_fiyat = settings.get('motorin_fiyat')
        adblue_fiyat = settings.get('adblue_fiyat')
        cari_fiyatlar = settings.get('cari_fiyatlar', {})

        # Yakıt
        for row in yakit_rows:
            p = row['plaka']
            ay = extract_month(row['islem_tarihi'])
            stok = (row['stok_adi'] or '').upper()
            
            if 'ADBLUE' in stok and adblue_fiyat:
                gider = float(row['toplam_yakit_miktari'] or 0) * adblue_fiyat
            elif 'ADBLUE' not in stok and motorin_fiyat:
                gider = float(row['toplam_yakit_miktari'] or 0) * motorin_fiyat
            else:
                gider = float(row['toplam_gider'] or 0)

            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['yakit_gider'] += gider

            if ay not in aylik_veriler:
                aylik_veriler[ay] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0}
            aylik_veriler[ay]['yakit_gider'] += gider

        # Bakım
        for row in bakim_rows:
            p = row['plaka']
            ay = extract_month(row['tarih'])
            gider = float(row['toplam_bakim_gider'] or 0)

            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['bakim_gider'] += gider

            if ay not in aylik_veriler:
                aylik_veriler[ay] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0}
            aylik_veriler[ay]['bakim_gider'] += gider
            
        # Ceza
        for row in ceza_rows:
            p = row['plaka']
            ay = extract_month(row['tarih'])
            gider = float(row['toplam_ceza_gider'] or 0)

            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['ceza_gider'] += gider

            if ay not in aylik_veriler:
                aylik_veriler[ay] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0}
            aylik_veriler[ay]['ceza_gider'] += gider

        # Hasar
        for row in hasar_rows:
            p = row['plaka']
            ay = extract_month(row['tarih'])
            gider = float(row['toplam_hasar_gider'] or 0)

            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['hasar_gider'] += gider

            if ay not in aylik_veriler:
                aylik_veriler[ay] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0}
            aylik_veriler[ay]['hasar_gider'] += gider

        # Gelir (Ağırlık)
        for row in agirlik_rows:
            p = row['plaka']
            ay = extract_month(row['tarih'])
            cari = (row['cari_adi'] or '').strip()
            
            # Fiyat belirleme (Customer matching)
            fiyat = 0.5 # Default multiplier if not found
            if cari_fiyatlar:
                # Case-insensitive substring matching
                for c_name, c_price in cari_fiyatlar.items():
                    if c_name.upper() in cari.upper() or cari.upper() in c_name.upper():
                        fiyat = c_price
                        break
                        
            gelir = float(row['toplam_agirlik'] or 0) * fiyat

            if p not in plaka_veriler:
                plaka_veriler[p] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0, 'ana_malzeme': 'Bilinmiyor'}
            plaka_veriler[p]['gelir'] += gelir
            plaka_veriler[p]['ana_malzeme'] = row['ana_malzeme'] or 'Bilinmiyor'

            if ay not in aylik_veriler:
                aylik_veriler[ay] = {'gelir': 0, 'yakit_gider': 0, 'bakim_gider': 0, 'ceza_gider': 0, 'hasar_gider': 0}
            aylik_veriler[ay]['gelir'] += gelir

            cari_display = cari if cari else 'Bilinmeyen Müşteri'
            if cari_display not in cari_veriler:
                cari_veriler[cari_display] = {'gelir': 0}
            cari_veriler[cari_display]['gelir'] += gelir

        toplam_gelir = sum(v['gelir'] for v in plaka_veriler.values())
        toplam_yakit_gider = sum(v['yakit_gider'] for v in plaka_veriler.values())
        toplam_bakim_gider = sum(v['bakim_gider'] for v in plaka_veriler.values())
        toplam_ceza_gider = sum(v['ceza_gider'] for v in plaka_veriler.values())
        toplam_hasar_gider = sum(v['hasar_gider'] for v in plaka_veriler.values())
        toplam_gider = toplam_yakit_gider + toplam_bakim_gider + toplam_ceza_gider + toplam_hasar_gider
        
        net_kar = toplam_gelir - toplam_gider
        kar_marji = (net_kar / toplam_gelir * 100) if toplam_gelir > 0 else 0

        plaka_bazli = []
        for p, v in plaka_veriler.items():
            net = v['gelir'] - (v['yakit_gider'] + v['bakim_gider'] + v['ceza_gider'] + v['hasar_gider'])
            marji = (net / v['gelir'] * 100) if v['gelir'] > 0 else 0
            plaka_bazli.append({
                'plaka': p,
                'gelir': v['gelir'],
                'yakit_gider': v['yakit_gider'],
                'bakim_gider': v['bakim_gider'],
                'ceza_gider': v['ceza_gider'],
                'hasar_gider': v['hasar_gider'],
                'toplam_gider': (v['yakit_gider'] + v['bakim_gider'] + v['ceza_gider'] + v['hasar_gider']),
                'net_kar': net,
                'kar_marji': marji,
                'ana_malzeme': v['ana_malzeme']
            })
        
        plaka_bazli.sort(key=lambda x: x['net_kar'], reverse=True)

        aylar = sorted([ay for ay in aylik_veriler.keys() if ay != 'Bilinmiyor'])[-12:] # Son 12 ay
        aylik_trend = {
            'aylar': aylar,
            'gelir': [aylik_veriler[ay]['gelir'] for ay in aylar],
            'yakit_gider': [aylik_veriler[ay]['yakit_gider'] for ay in aylar],
            'bakim_gider': [aylik_veriler[ay]['bakim_gider'] for ay in aylar]
        }

        # Cari bazlı liste
        cari_bazli = [{'cari': k, 'gelir': v['gelir']} for k, v in cari_veriler.items()]
        cari_bazli.sort(key=lambda x: x['gelir'], reverse=True)

        return {
            'status': 'success',
            'toplam_gelir': toplam_gelir,
            'toplam_yakit_gider': toplam_yakit_gider,
            'toplam_bakim_gider': toplam_bakim_gider,
            'toplam_ceza_gider': toplam_ceza_gider,
            'toplam_hasar_gider': toplam_hasar_gider,
            'toplam_gider': toplam_gider,
            'net_kar': net_kar,
            'kar_marji': kar_marji,
            'plaka_bazli': plaka_bazli,
            'aylik_trend': aylik_trend,
            'cari_bazli': cari_bazli
        }

    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'message': str(e) + " - " + traceback.format_exc()
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
                SUM(CASE WHEN birim IN ('Kg', 'kg', 'KG') THEN miktar ELSE miktar * 1000.0 END) as toplam_tonaj,
                COUNT(*) as yuklenme_sayisi,
                AVG(CASE WHEN birim IN ('Kg', 'kg', 'KG') THEN miktar ELSE miktar * 1000.0 END) as ort_tonaj_yuklenme
            FROM agirlik
            WHERE plaka = ? {tarih_filtre_agirlik}
            AND miktar IS NOT NULL AND miktar > 0
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
                fatura_no, garanti_durumu, durum
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get('garanti_durumu'),
            data.get('durum', 'Tamamlandı')
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Bakım kaydı başarıyla eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def update_bakim_maliyet(bakim_id, data):
    """Mevcut bir bakım kaydına servis ve maliyet bilgilerini ekleyip kapat"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        iscilik = float(data.get('iscilik_maliyeti') or 0)
        parca = float(data.get('parca_maliyeti') or 0)
        toplam_maliyet = float(data.get('maliyet') or (iscilik + parca))
        
        cursor.execute('''
            UPDATE bakim SET 
                servis_adi = ?, 
                servis_giris_tarihi = ?, 
                servis_cikis_tarihi = ?, 
                iscilik_maliyeti = ?, 
                parca_maliyeti = ?, 
                maliyet = ?, 
                fatura_no = ?, 
                garanti_durumu = ?,
                bir_sonraki_bakim_km = ?,
                bir_sonraki_bakim_tarih = ?,
                durum = 'Tamamlandı'
            WHERE id = ?
        ''', (
            data.get('servis_adi'),
            data.get('servis_giris_tarihi'),
            data.get('servis_cikis_tarihi'),
            iscilik,
            parca,
            toplam_maliyet,
            data.get('fatura_no'),
            data.get('garanti_durumu'),
            data.get('bir_sonraki_bakim_km'),
            data.get('bir_sonraki_bakim_tarih'),
            bakim_id
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Bakım kaydı başarıyla güncellendi ve kapatıldı'}
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

# --- ŞOFÖR YÖNETİMİ (AŞAMA 2) ---

def get_soforler(aktif_sadece=False):
    """Tüm şoförleri getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if aktif_sadece:
            cursor.execute('SELECT * FROM soforler WHERE aktif = 1 ORDER BY ad_soyad')
        else:
            cursor.execute('SELECT * FROM soforler ORDER BY ad_soyad')
            
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Şoförler getirilemedi: {e}")
        return []

def add_sofor(data):
    """Yeni şoför ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO soforler (ad_soyad, telefon, tc_no, aktif)
            VALUES (?, ?, ?, ?)
        ''', (
            data.get('ad_soyad'),
            data.get('telefon'),
            data.get('tc_no'),
            int(data.get('aktif', 1))
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Şoför başarıyla eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def update_sofor(sofor_id, data):
    """Şoför bilgilerini güncelle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE soforler SET 
                ad_soyad = ?, 
                telefon = ?, 
                tc_no = ?, 
                aktif = ?
            WHERE id = ?
        ''', (
            data.get('ad_soyad'),
            data.get('telefon'),
            data.get('tc_no'),
            int(data.get('aktif', 1)),
            sofor_id
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Şoför başarıyla güncellendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def delete_sofor(sofor_id):
    """Şoför kaydını sil"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM soforler WHERE id = ?', (sofor_id,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Şoför silindi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# --- HASAR VE CEZA YÖNETİMİ (AŞAMA 3) ---

def get_cezalar():
    """Tüm cezaları getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.ad_soyad as sofor_adi 
            FROM cezalar c
            LEFT JOIN soforler s ON c.sofor_id = s.id
            ORDER BY c.tarih DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Cezalar getirilemedi: {e}")
        return []

def add_ceza(data):
    """Yeni trafik cezası ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cezalar (plaka, sofor_id, tarih, tutar, aciklama, odeme_durumu)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('plaka'),
            data.get('sofor_id') if data.get('sofor_id') else None,
            data.get('tarih'),
            float(data.get('tutar', 0)),
            data.get('aciklama'),
            data.get('odeme_durumu', 'Ödenmedi')
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Ceza başarıyla eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def delete_ceza(ceza_id):
    """Ceza kaydını sil"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cezalar WHERE id = ?', (ceza_id,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Ceza silindi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_hasarlar():
    """Tüm hasarları getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, s.ad_soyad as sofor_adi 
            FROM hasarlar h
            LEFT JOIN soforler s ON h.sofor_id = s.id
            ORDER BY h.tarih DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Hasarlar getirilemedi: {e}")
        return []

def add_hasar(data):
    """Yeni kaza/hasar ekle"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO hasarlar (plaka, sofor_id, tarih, tutar, aciklama, sigorta_karsiladi_mi, konum_enlem, konum_boylam, fotograf_yolu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('plaka'),
            data.get('sofor_id') if data.get('sofor_id') else None,
            data.get('tarih'),
            float(data.get('tutar', 0)),
            data.get('aciklama'),
            int(data.get('sigorta_karsiladi_mi', 0)),
            data.get('konum_enlem'),
            data.get('konum_boylam'),
            data.get('fotograf_yolu')
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Hasar kaydı başarıyla eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def delete_hasar(hasar_id):
    """Hasar kaydını sil"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM hasarlar WHERE id = ?', (hasar_id,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Hasar kaydı silindi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# --- LASTİK YÖNETİMİ (AŞAMA 4) ---

def get_lastikler(aktif_sadece=False):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if aktif_sadece:
            cursor.execute('SELECT * FROM lastikler WHERE aktif = 1 ORDER BY id DESC')
        else:
            cursor.execute('SELECT * FROM lastikler ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Lastikler getirilemedi: {e}")
        return []

def add_lastik(data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO lastikler (marka, ebat, seri_no, fiyat, alinma_tarihi, aktif)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            data.get('marka'),
            data.get('ebat'),
            data.get('seri_no'),
            float(data.get('fiyat', 0)),
            data.get('alinma_tarihi')
        ))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Lastik envantere eklendi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def delete_lastik(lastik_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE lastikler SET aktif = 0 WHERE id = ?', (lastik_id,))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Lastik envanterden silindi (pasife çekildi)'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_arac_lastikleri(plaka):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ald.*, l.marka, l.ebat, l.seri_no 
            FROM arac_lastik_durumu ald
            JOIN lastikler l ON ald.lastik_id = l.id
            WHERE ald.plaka = ? AND ald.sokulme_tarihi IS NULL
        ''', (plaka,))
        rows = cursor.fetchall()
        conn.close()
        return [dict_from_row(row) for row in rows]
    except Exception as e:
        print(f"Araç lastikleri getirilemedi: {e}")
        return []

def tak_lastik(plaka, lastik_id, pozisyon, takilma_tarihi, takilma_km):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eğer bu pozisyonda zaten takılı bir lastik varsa onu sökülmüş olarak işaretle
        cursor.execute('''
            UPDATE arac_lastik_durumu 
            SET sokulme_tarihi = ?, sokulme_km = ? 
            WHERE plaka = ? AND pozisyon = ? AND sokulme_tarihi IS NULL
        ''', (takilma_tarihi, takilma_km, plaka, pozisyon))
        
        # Yeni lastiği tak
        cursor.execute('''
            INSERT INTO arac_lastik_durumu (plaka, lastik_id, takilma_tarihi, takilma_km, pozisyon)
            VALUES (?, ?, ?, ?, ?)
        ''', (plaka, lastik_id, takilma_tarihi, takilma_km, pozisyon))
        
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': f'Lastik araca takıldı (Pozisyon: {pozisyon})'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def sok_lastik(durum_id, sokulme_tarihi, sokulme_km):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE arac_lastik_durumu 
            SET sokulme_tarihi = ?, sokulme_km = ? 
            WHERE id = ?
        ''', (sokulme_tarihi, sokulme_km, durum_id))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Lastik araçtan söküldü'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# --- ŞOFÖR PANELİ (PWA - AŞAMA 5) ---

def get_sofor_by_telefon(telefon):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soforler WHERE telefon = ? AND aktif = 1", (telefon,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row) if row else None
    except Exception as e:
        print(f"Şoför girişinde hata: {e}")
        return None

def get_aktif_sefer(sofor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM seferler WHERE sofor_id = ? AND durum = 'Aktif'", (sofor_id,))
        row = cursor.fetchone()
        conn.close()
        return dict_from_row(row) if row else None
    except Exception as e:
        print(f"Aktif sefer getirilemedi: {e}")
        return None

def baslat_sefer(sofor_id, plaka, baslangic_km):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO seferler (sofor_id, plaka, baslangic_zaman, baslangic_km, durum)
            VALUES (?, ?, ?, ?, 'Aktif')
        ''', (sofor_id, plaka, now, baslangic_km))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Sefer başlatıldı'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def bitir_sefer(sefer_id, bitis_km):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE seferler 
            SET bitis_zaman = ?, bitis_km = ?, durum = 'Tamamlandı'
            WHERE id = ?
        ''', (now, bitis_km, sefer_id))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Sefer tamamlandı'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def add_yakit_from_sofor(sofor_id, plaka, litre, fotograf_yolu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO yakit (plaka, sofor_id, yakit_miktari, islem_tarihi, fis_fotograf_yolu, stok_adi)
            VALUES (?, ?, ?, ?, ?, 'MOTORİN')
        ''', (plaka, sofor_id, litre, now, fotograf_yolu))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Yakıt fişi başarıyla kaydedildi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def add_ariza_from_sofor(sofor_id, plaka, aciklama, telefon):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            INSERT INTO bakim (plaka, bakim_tipi, yapilan_islem, tarih, maliyet, durum, bildiren_kisi, iletisim_tel)
            VALUES (?, 'Arıza/Onarım', ?, ?, 0, 'Açık', (SELECT ad_soyad FROM soforler WHERE id = ?), ?)
        ''', (plaka, aciklama, now, sofor_id, telefon))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Arıza kaydı oluşturuldu'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def add_evrak_from_sofor(sofor_id, plaka, evrak_tipi, aciklama, fotograf_yolu):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sofor_evraklari (sofor_id, plaka, evrak_tipi, aciklama, fotograf_yolu)
            VALUES (?, ?, ?, ?, ?)
        ''', (sofor_id, plaka, evrak_tipi, aciklama, fotograf_yolu))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Evrak başarıyla gönderildi'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_saha_bildirimleri():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Evraklar
        cursor.execute('''
            SELECT e.*, s.ad_soyad as sofor_adi, e.created_at as tarih_sirala 
            FROM sofor_evraklari e 
            LEFT JOIN soforler s ON e.sofor_id = s.id 
            ORDER BY e.created_at DESC LIMIT 50
        ''')
        evraklar = [dict_from_row(r) for r in cursor.fetchall()]
        
        # 2. Arızalar (Açık olanlar)
        cursor.execute('''
            SELECT b.*, b.tarih as tarih_sirala 
            FROM bakim b 
            WHERE b.durum = 'Açık' AND b.bakim_tipi = 'Arıza/Onarım' 
            ORDER BY b.tarih DESC LIMIT 50
        ''')
        arizalar = [dict_from_row(r) for r in cursor.fetchall()]
        
        # 3. Hasarlar (Fotoğraflı veya Konumlu)
        cursor.execute('''
            SELECT h.*, s.ad_soyad as sofor_adi, h.created_at as tarih_sirala 
            FROM hasarlar h 
            LEFT JOIN soforler s ON h.sofor_id = s.id 
            WHERE h.fotograf_yolu IS NOT NULL OR h.konum_enlem IS NOT NULL
            ORDER BY h.tarih DESC LIMIT 50
        ''')
        hasarlar = [dict_from_row(r) for r in cursor.fetchall()]
        
        # 4. Yakıt Fişleri
        cursor.execute('''
            SELECT y.*, s.ad_soyad as sofor_adi, y.created_at as tarih_sirala 
            FROM yakit y 
            LEFT JOIN soforler s ON y.sofor_id = s.id 
            WHERE y.fis_fotograf_yolu IS NOT NULL 
            ORDER BY y.created_at DESC LIMIT 50
        ''')
        yakit_fisleri = [dict_from_row(r) for r in cursor.fetchall()]
        
        conn.close()
        return {
            'evraklar': evraklar,
            'arizalar': arizalar,
            'hasarlar': hasarlar,
            'yakit_fisleri': yakit_fisleri
        }
    except Exception as e:
        print(f"Saha bildirimleri getirilirken hata: {e}")
        return {'evraklar': [], 'arizalar': [], 'hasarlar': [], 'yakit_fisleri': []}
