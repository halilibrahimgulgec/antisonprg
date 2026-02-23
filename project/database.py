import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'kargo_data.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS yakit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            islem_tarihi TEXT,
            saat TEXT,
            yakit_miktari REAL,
            birim_fiyat REAL,
            satir_tutari REAL,
            stok_adi TEXT,
            km_bilgisi REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agirlik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            tarih TEXT,
            miktar REAL,
            net_agirlik REAL,
            cari_adi TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS araclar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT UNIQUE NOT NULL,
            sahip TEXT DEFAULT 'Bizim',
            arac_tipi TEXT DEFAULT 'Kargo',
            aktif INTEGER DEFAULT 1,
            notlar TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bakim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT NOT NULL,
            bakim_tipi TEXT,
            maliyet REAL,
            tarih TEXT,
            aciklama TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS takip (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT,
            tarih TEXT,
            km_baslangic REAL,
            km_bitis REAL,
            km_fark REAL,
            sure_dakika REAL,
            surucu TEXT,
            guzergah TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')

    conn.commit()
    conn.close()


def get_db_stats():
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}

    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM yakit")
        stats['yakit_kayit'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COALESCE(SUM(yakit_miktari), 0) as total FROM yakit WHERE yakit_miktari > 0")
        stats['toplam_yakit'] = round(cursor.fetchone()['total'], 2)

        cursor.execute("SELECT COALESCE(SUM(satir_tutari), 0) as total FROM yakit WHERE satir_tutari > 0")
        stats['toplam_maliyet'] = round(cursor.fetchone()['total'], 2)

        cursor.execute("SELECT COUNT(DISTINCT plaka) as cnt FROM yakit")
        stats['plaka_sayisi'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM agirlik")
        stats['agirlik_kayit'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COALESCE(SUM(net_agirlik), 0) as total FROM agirlik WHERE net_agirlik > 0")
        stats['toplam_agirlik'] = round(cursor.fetchone()['total'], 2)

        cursor.execute("SELECT COUNT(*) as cnt FROM araclar WHERE aktif = 1")
        stats['aktif_arac'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM bakim")
        stats['bakim_kayit'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COALESCE(SUM(maliyet), 0) as total FROM bakim")
        stats['toplam_bakim_maliyet'] = round(cursor.fetchone()['total'], 2)

    except Exception as e:
        print(f"Stats error: {e}")

    conn.close()
    return stats


def get_yakit_data(plaka=None, baslangic=None, bitis=None, arac_tipi=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT y.*, a.arac_tipi, a.sahip
        FROM yakit y
        LEFT JOIN araclar a ON y.plaka = a.plaka
        WHERE y.yakit_miktari > 0
    '''
    params = []

    if plaka:
        query += " AND y.plaka = ?"
        params.append(plaka)
    if baslangic:
        query += " AND y.islem_tarihi >= ?"
        params.append(baslangic)
    if bitis:
        query += " AND y.islem_tarihi <= ?"
        params.append(bitis)
    if arac_tipi:
        query += " AND a.arac_tipi = ?"
        params.append(arac_tipi)

    query += " ORDER BY y.islem_tarihi DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_yakit_aylik_ozet(arac_tipi=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            strftime('%Y-%m', y.islem_tarihi) as ay,
            COUNT(*) as islem_sayisi,
            SUM(y.yakit_miktari) as toplam_yakit,
            SUM(y.satir_tutari) as toplam_tutar,
            COUNT(DISTINCT y.plaka) as plaka_sayisi,
            AVG(y.birim_fiyat) as ort_birim_fiyat
        FROM yakit y
        LEFT JOIN araclar a ON y.plaka = a.plaka
        WHERE y.yakit_miktari > 0
    '''
    params = []

    if arac_tipi:
        query += " AND a.arac_tipi = ?"
        params.append(arac_tipi)

    query += " GROUP BY strftime('%Y-%m', y.islem_tarihi) ORDER BY ay DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_plaka_listesi():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT y.plaka, a.arac_tipi, a.sahip, a.aktif
        FROM yakit y
        LEFT JOIN araclar a ON y.plaka = a.plaka
        ORDER BY y.plaka
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_plaka_ozet(plaka):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as islem_sayisi,
            SUM(yakit_miktari) as toplam_yakit,
            SUM(satir_tutari) as toplam_maliyet,
            AVG(yakit_miktari) as ort_yakit,
            MIN(islem_tarihi) as ilk_tarih,
            MAX(islem_tarihi) as son_tarih
        FROM yakit
        WHERE plaka = ? AND yakit_miktari > 0
    ''', (plaka,))
    yakit_ozet = dict(cursor.fetchone())

    cursor.execute('''
        SELECT
            COUNT(*) as sefer_sayisi,
            SUM(net_agirlik) as toplam_agirlik,
            AVG(net_agirlik) as ort_agirlik
        FROM agirlik
        WHERE plaka = ? AND net_agirlik > 0
    ''', (plaka,))
    agirlik_ozet = dict(cursor.fetchone())

    conn.close()
    return {'yakit': yakit_ozet, 'agirlik': agirlik_ozet}


def get_araclar():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*,
            (SELECT COUNT(*) FROM yakit y WHERE y.plaka = a.plaka) as yakit_islem,
            (SELECT COALESCE(SUM(yakit_miktari), 0) FROM yakit y WHERE y.plaka = a.plaka AND y.yakit_miktari > 0) as toplam_yakit,
            (SELECT COALESCE(SUM(satir_tutari), 0) FROM yakit y WHERE y.plaka = a.plaka AND y.satir_tutari > 0) as toplam_maliyet
        FROM araclar a
        ORDER BY a.plaka
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_arac(plaka, sahip, arac_tipi, aktif, notlar=''):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO araclar (plaka, sahip, arac_tipi, aktif, notlar)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(plaka) DO UPDATE SET
            sahip = excluded.sahip,
            arac_tipi = excluded.arac_tipi,
            aktif = excluded.aktif,
            notlar = excluded.notlar
    ''', (plaka, sahip, arac_tipi, aktif, notlar))
    conn.commit()
    conn.close()


def ensure_arac_exists(plaka):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO araclar (plaka, sahip, arac_tipi, aktif) VALUES (?, 'Bizim', 'Kargo', 1)",
        (plaka,)
    )
    conn.commit()
    conn.close()


def add_bakim(plaka, bakim_tipi, maliyet, tarih, aciklama):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bakim (plaka, bakim_tipi, maliyet, tarih, aciklama)
        VALUES (?, ?, ?, ?, ?)
    ''', (plaka, bakim_tipi, maliyet, tarih, aciklama))
    conn.commit()
    conn.close()


def get_bakim_listesi(plaka=None):
    conn = get_connection()
    cursor = conn.cursor()
    if plaka:
        cursor.execute("SELECT * FROM bakim WHERE plaka = ? ORDER BY tarih DESC", (plaka,))
    else:
        cursor.execute("SELECT * FROM bakim ORDER BY tarih DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_muhasebe_ozet(ay=None):
    conn = get_connection()
    cursor = conn.cursor()

    if ay:
        yakit_query = '''
            SELECT
                a.arac_tipi,
                COUNT(*) as islem,
                SUM(y.yakit_miktari) as yakit,
                SUM(y.satir_tutari) as tutar
            FROM yakit y
            LEFT JOIN araclar a ON y.plaka = a.plaka
            WHERE strftime('%Y-%m', y.islem_tarihi) = ? AND y.yakit_miktari > 0
            GROUP BY a.arac_tipi
        '''
        cursor.execute(yakit_query, (ay,))
    else:
        yakit_query = '''
            SELECT
                a.arac_tipi,
                COUNT(*) as islem,
                SUM(y.yakit_miktari) as yakit,
                SUM(y.satir_tutari) as tutar
            FROM yakit y
            LEFT JOIN araclar a ON y.plaka = a.plaka
            WHERE y.yakit_miktari > 0
            GROUP BY a.arac_tipi
        '''
        cursor.execute(yakit_query)

    yakit_tipler = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {'yakit_tipler': yakit_tipler}


def get_kargo_verimlilik():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            y.plaka,
            SUM(y.yakit_miktari) as toplam_yakit,
            SUM(a.net_agirlik) as toplam_agirlik,
            CASE WHEN SUM(a.net_agirlik) > 0
                 THEN ROUND(SUM(y.yakit_miktari) / SUM(a.net_agirlik), 4)
                 ELSE NULL END as litre_per_ton
        FROM yakit y
        LEFT JOIN agirlik a ON y.plaka = a.plaka
        LEFT JOIN araclar ar ON y.plaka = ar.plaka
        WHERE y.yakit_miktari > 0
          AND (ar.arac_tipi = 'Kargo' OR ar.arac_tipi IS NULL)
        GROUP BY y.plaka
        HAVING toplam_yakit > 0
        ORDER BY litre_per_ton DESC
    ''')

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ai_context():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            y.plaka,
            strftime('%Y-%m', y.islem_tarihi) as ay,
            SUM(y.yakit_miktari) as toplam_yakit,
            SUM(y.satir_tutari) as toplam_maliyet,
            COUNT(*) as islem_sayisi
        FROM yakit y
        WHERE y.yakit_miktari > 0
        GROUP BY y.plaka, strftime('%Y-%m', y.islem_tarihi)
        ORDER BY ay DESC, toplam_yakit DESC
        LIMIT 50
    ''')
    yakit_ozet = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT plaka, arac_tipi, sahip, aktif FROM araclar ORDER BY plaka
    ''')
    araclar = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT plaka, SUM(net_agirlik) as toplam_ton, COUNT(*) as sefer
        FROM agirlik WHERE net_agirlik > 0
        GROUP BY plaka
        ORDER BY toplam_ton DESC
        LIMIT 20
    ''')
    agirlik_ozet = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        'yakit_ozet': yakit_ozet,
        'araclar': araclar,
        'agirlik_ozet': agirlik_ozet
    }
