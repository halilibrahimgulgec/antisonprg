import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_cors import CORS
from flask_babel import Babel, gettext as _
from datetime import datetime
import logging
from dotenv import load_dotenv
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-here'

# Babel Configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'tr'
app.config['BABEL_SUPPORTED_LOCALES'] = ['tr', 'en', 'de']

def get_locale():
    if 'lang' in session:
        return session['lang']
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

babel = Babel(app, locale_selector=get_locale)

# Authentication Check
@app.before_request
def check_auth():
    # Public routes that don't require login
    public_routes = ['login', 'static', 'set_language']
    
    # If request doesn't match a route or is a public route, let it pass
    if request.endpoint is None or request.endpoint in public_routes:
        return None
        
    # If user is in session, allow access
    if 'user_id' in session:
        return None
        
    # If not logged in, redirect to login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı giriş sayfası"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        from database import verify_user
        user = verify_user(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Hoş geldiniz, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Kullanıcı çıkış işlemi"""
    session.clear()
    flash('Başarıyla çıkış yapıldı.', 'success')
    return redirect(url_for('login'))

@app.route('/admin/users')
def list_users():
    """Kullanıcı yönetim sayfası"""
    if session.get('role') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok.', 'error')
        return redirect(url_for('index'))
    
    from database import get_all_users
    users = get_all_users()
    return render_template('users.html', users=users)

@app.route('/admin/user/add', methods=['POST'])
def add_user():
    """Yeni kullanıcı ekle"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if not username or not password:
        flash('Kullanıcı adı ve şifre gereklidir.', 'error')
        return redirect(url_for('list_users'))
        
    from database import add_new_user
    if add_new_user(username, password, role):
        flash(f'Kullanıcı {username} başarıyla eklendi.', 'success')
    else:
        flash('Kullanıcı eklenirken bir hata oluştu (Kullanıcı adı zaten var olabilir).', 'error')
        
    return redirect(url_for('list_users'))

@app.route('/admin/user/delete/<int:user_id>')
def remove_user(user_id):
    """Kullanıcıyı sil"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    if user_id == session.get('user_id'):
        flash('Kendi kullanıcınızı silemezsiniz.', 'error')
        return redirect(url_for('list_users'))
        
    from database import delete_user
    if delete_user(user_id):
        flash('Kullanıcı başarıyla silindi.', 'success')
    else:
        flash('Kullanıcı silinirken bir hata oluştu.', 'error')
        
    return redirect(url_for('list_users'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

# Jinja2 template'lere Python built-in fonksiyonları ekle
app.jinja_env.globals.update(zip=zip)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def tr_format(value, decimals=2, is_int=False):
    """Sayıları Türkçe formatına çevirir (Binlik: . , Ondalık: ,)"""
    if value is None or (isinstance(value, str) and value == 'N/A'):
        return 'N/A'
    try:
        val = float(value)
        if is_int:
            return "{:,.0f}".format(val).replace(',', '.')
        
        # Önce standart formatla (binlik virgül, ondalık nokta)
        fmt = "{:,." + str(decimals) + "f}"
        s = fmt.format(val)
        # Virgül ve noktayı yer değiştir
        return s.replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return str(value)

@app.route('/')
def index():
    """Ana sayfa - Yakıt tahmin sistemi"""
    from database import get_database_info, get_statistics
    db_info = get_database_info()
    db_info['stats'] = get_statistics()
    return render_template('index.html', db_info=db_info)

@app.route('/muhasebe')
def muhasebe():
    """Muhasebe sayfası"""
    return render_template('muhasebe.html')

@app.route('/api/plakalar')
def api_plakalar():
    """Plaka listesi API - araç tipine göre filtrelenebilir"""
    try:
        import sqlite3
        conn = sqlite3.connect('kargo_data.db')
        cursor = conn.cursor()

        arac_tipi = request.args.get('tip')

        if arac_tipi == 'binek':
            cursor.execute('''
                SELECT DISTINCT y.plaka
                FROM yakit y
                JOIN araclar a ON y.plaka = a.plaka
                WHERE a.arac_tipi = 'BİNEK ARAÇ'
                AND a.aktif = 1
                AND a.sahip = 'BİZİM'
                ORDER BY y.plaka
            ''')
        elif arac_tipi == 'is_makinesi':
            cursor.execute('''
                SELECT DISTINCT y.plaka
                FROM yakit y
                JOIN araclar a ON y.plaka = a.plaka
                WHERE a.arac_tipi = 'İŞ MAKİNESİ'
                AND a.aktif = 1
                AND a.sahip = 'BİZİM'
                ORDER BY y.plaka
            ''')
        elif arac_tipi == 'kargo':
            cursor.execute('''
                SELECT DISTINCT y.plaka
                FROM yakit y
                JOIN araclar a ON y.plaka = a.plaka
                WHERE a.arac_tipi = 'KARGO ARACI'
                AND a.aktif = 1
                AND a.sahip = 'BİZİM'
                ORDER BY y.plaka
            ''')
        else:
            cursor.execute('SELECT DISTINCT plaka FROM yakit ORDER BY plaka')

        plakalar = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({'plakalar': plakalar})
    except Exception as e:
        return jsonify({'plakalar': [], 'error': str(e)})

@app.route('/api/fetch-mail', methods=['POST'])
def api_fetch_mail():
    """Mailden Excel dosyalarını çek"""
    try:
        from mail_fetcher import fetch_email_attachments
        result = fetch_email_attachments()
        
        if result['status'] == 'error':
            return jsonify({'success': False, 'message': result['message']}), 500
        
        return jsonify({'success': True, 'message': result['message'], 'details': result.get('details')})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/save-mail-settings', methods=['POST'])
def save_mail_settings():
    """Mail ayarlarını .env dosyasına kaydet"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        sender = data.get('sender') or ''
        
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        # Mevcut içeriği oku
        new_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
                
            updated_keys = set()
            for line in lines:
                if line.startswith('MAIL_USERNAME='):
                    new_lines.append(f'MAIL_USERNAME={username}\n')
                    updated_keys.add('MAIL_USERNAME')
                elif line.startswith('MAIL_PASSWORD='):
                    new_lines.append(f'MAIL_PASSWORD={password}\n')
                    updated_keys.add('MAIL_PASSWORD')
                elif line.startswith('MAIL_SENDER_FILTER='):
                    new_lines.append(f'MAIL_SENDER_FILTER={sender}\n')
                    updated_keys.add('MAIL_SENDER_FILTER')
                else:
                    new_lines.append(line)
            
            # Eğer anahtarlar yoksa ekle
            if 'MAIL_USERNAME' not in updated_keys: new_lines.append(f'MAIL_USERNAME={username}\n')
            if 'MAIL_PASSWORD' not in updated_keys: new_lines.append(f'MAIL_PASSWORD={password}\n')
            if 'MAIL_SENDER_FILTER' not in updated_keys: new_lines.append(f'MAIL_SENDER_FILTER={sender}\n')
            
        else:
            # Dosya yoksa oluştur
            new_lines = [
                f'MAIL_USERNAME={username}\n',
                f'MAIL_PASSWORD={password}\n',
                f'MAIL_SENDER_FILTER={sender}\n'
            ]
            
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
            
        # Environment variables'ı yenile
        load_dotenv(override=True)
        
        return jsonify({'success': True, 'message': 'Ayarlar kaydedildi'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Veritabanından analiz yap"""
    try:
        from model_analyzer import analyze_from_database
        from database import get_database_info

        db_info = get_database_info()
        if not db_info.get('exists'):
            flash('❌ Veritabanı dosyası bulunamadı! Önce python excel_to_sqlite.py komutunu çalıştırın.', 'error')
            return redirect(url_for('index'))

        # Filtreleri al
        baslangic_tarihi = request.form.get('baslangic_tarihi') or None
        bitis_tarihi = request.form.get('bitis_tarihi') or None
        plaka = request.form.get('plaka') or None
        dahil_taseron = request.form.get('dahil_taseron') == '1'

        # Filtreleri kaydet
        session['filter_baslangic'] = baslangic_tarihi
        session['filter_bitis'] = bitis_tarihi
        session['filter_plaka'] = plaka
        session['dahil_taseron'] = dahil_taseron

        analysis_result = analyze_from_database(baslangic_tarihi, bitis_tarihi, plaka, dahil_taseron)

        if analysis_result['status'] == 'error':
            flash(f'❌ Veritabanı analiz hatası: {analysis_result["error"]}', 'error')
            return redirect(url_for('index'))

        if analysis_result['records'] == 0:
            flash('❌ Veritabanında hiç kayıt yok! Excel dosyalarınızı python excel_to_sqlite.py ile yükleyin.', 'error')
            return redirect(url_for('index'))

        plakalar = []
        tahminler = []

        if analysis_result['toplam_yakit'] > 0 and len(analysis_result.get('plakalar', [])) > 0:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()

            query = '''
                SELECT
                    y.plaka,
                    SUM(y.yakit_miktari) as toplam_yakit,
                    SUM(y.km_bilgisi) as toplam_km,
                    AVG(y.yakit_miktari) as ortalama_yakit
                FROM yakit y
                INNER JOIN araclar a ON y.plaka = a.plaka
                WHERE y.yakit_miktari IS NOT NULL
                AND y.yakit_miktari > 0
                AND a.aktif = 1
                AND a.arac_tipi = 'KARGO ARACI'
            '''
            
            query_params = []
            if not dahil_taseron:
                query += " AND a.sahip = 'BİZİM'"
            
            if baslangic_tarihi:
                query += " AND y.islem_tarihi >= ?"
                query_params.append(baslangic_tarihi)
            if bitis_tarihi:
                query += " AND y.islem_tarihi <= ?"
                query_params.append(bitis_tarihi)
            if plaka:
                query += " AND y.plaka = ?"
                query_params.append(plaka)
                
            query += " GROUP BY y.plaka ORDER BY ortalama_yakit DESC"
            cursor.execute(query, query_params)

            yakit_rows = cursor.fetchall()
            arac_detaylari = []

            for row in yakit_rows:
                plaka = row['plaka']
                toplam_yakit = float(row['toplam_yakit'])
                ortalama_yakit = float(row['ortalama_yakit'])

                # KM Hesabı (Odometre farkı)
                cursor.execute('''
                    SELECT (MAX(km_bilgisi) - MIN(km_bilgisi)) as fark
                    FROM yakit
                    WHERE plaka = ?
                    AND km_bilgisi IS NOT NULL AND km_bilgisi > 0
                ''', (plaka,))
                km_fark_row = cursor.fetchone()
                toplam_km = float(km_fark_row['fark'] or 0)
                
                # Eğer odometre farkı 0 ise alternatif olarak km_fark toplamını dene
                if toplam_km == 0:
                     cursor.execute('SELECT SUM(km_fark) as toplam FROM yakit WHERE plaka = ?', (plaka,))
                     toplam_km = float(cursor.fetchone()['toplam'] or 0)

                # Ağırlık ve SEFER bilgisini BİRİM BAZINDA agirlik tablosundan al
                ag_query = '''
                    SELECT
                        birim,
                        SUM(miktar) as toplam,
                        COUNT(*) as sefer_sayisi
                    FROM agirlik
                    WHERE plaka = ?
                    AND miktar IS NOT NULL
                    AND miktar > 0
                '''
                ag_params = [plaka]
                if baslangic_tarihi:
                    ag_query += " AND tarih >= ?"
                    ag_params.append(baslangic_tarihi)
                if bitis_tarihi:
                    ag_query += " AND tarih <= ?"
                    ag_params.append(bitis_tarihi)
                
                ag_query += " GROUP BY birim"
                cursor.execute(ag_query, ag_params)

                agirlik_rows = cursor.fetchall()

                # Birim bazında verileri ayır
                kg_data = {'toplam': 0, 'sefer': 0}
                m2_data = {'toplam': 0, 'sefer': 0}
                m3_data = {'toplam': 0, 'sefer': 0}
                adet_data = {'toplam': 0, 'sefer': 0}
                mt_data = {'toplam': 0, 'sefer': 0}

                for ag_row in agirlik_rows:
                    birim = ag_row['birim'] if ag_row['birim'] else ''
                    toplam = float(ag_row['toplam']) if ag_row['toplam'] else 0
                    sefer = int(ag_row['sefer_sayisi']) if ag_row['sefer_sayisi'] else 0

                    if birim.upper() == 'KG':
                        kg_data = {'toplam': toplam, 'sefer': sefer}
                    elif birim.upper() == 'M2':
                        m2_data = {'toplam': toplam, 'sefer': sefer}
                    elif birim.upper() == 'M3':
                        m3_data = {'toplam': toplam, 'sefer': sefer}
                    elif birim.upper() == 'ADET':
                        adet_data = {'toplam': toplam, 'sefer': sefer}
                    elif birim.upper() == 'MT':
                        mt_data = {'toplam': toplam, 'sefer': sefer}

                # Sefer sayısı standardizasyonu: Kantar kaydı yoksa yakıt alım sayısını kullan
                sefer_sayisi = kg_data['sefer'] if kg_data['sefer'] > 0 else (int(row['sefer_sayisi']) if 'sefer_sayisi' in row.keys() and row['sefer_sayisi'] else 0)
                if sefer_sayisi == 0:
                    cursor.execute('SELECT COUNT(*) as count FROM yakit WHERE plaka = ?', (plaka,))
                    sefer_sayisi = cursor.fetchone()['count']

                # Hesaplamalar
                km_litre_orani = round(toplam_km / toplam_yakit, 2) if toplam_yakit > 0 and toplam_km > 0 else None
                kg_litre_orani = round(kg_data['toplam'] / toplam_yakit, 2) if toplam_yakit > 0 and kg_data['toplam'] > 0 else None

                plakalar.append(plaka)
                tahminler.append(round(ortalama_yakit, 2))

                arac_detaylari.append({
                    'plaka': plaka,
                    'toplam_yakit': round(toplam_yakit, 2),
                    'toplam_km': round(toplam_km, 2) if toplam_km > 0 else None,
                    'sefer_sayisi': sefer_sayisi,
                    'kg_toplam': round(kg_data['toplam'], 2) if kg_data['toplam'] > 0 else None,
                    'kg_sefer': kg_data['sefer'],
                    'm2_toplam': round(m2_data['toplam'], 2) if m2_data['toplam'] > 0 else None,
                    'm2_sefer': m2_data['sefer'],
                    'm3_toplam': round(m3_data['toplam'], 2) if m3_data['toplam'] > 0 else None,
                    'm3_sefer': m3_data['sefer'],
                    'adet_toplam': int(adet_data['toplam']) if adet_data['toplam'] > 0 else None,
                    'adet_sefer': adet_data['sefer'],
                    'mt_toplam': round(mt_data['toplam'], 2) if mt_data['toplam'] > 0 else None,
                    'mt_sefer': mt_data['sefer'],
                    'ortalama_yakit': round(ortalama_yakit, 2),
                    'km_litre_orani': km_litre_orani,
                    'kg_litre_orani': kg_litre_orani
                })

            conn.close()
        else:
            flash(f'❌ Veritabanında yakıt verisi bulunamadı!', 'error')
            return redirect(url_for('index'))

        flash('✅ Veritabanı analizi tamamlandı!', 'success')

        insights = {
            'toplam_yakit': analysis_result['toplam_yakit'],
            'toplam_maliyet': analysis_result['toplam_maliyet'],
            'ortalama_fiyat': analysis_result['toplam_maliyet'] / analysis_result['toplam_yakit'] if analysis_result['toplam_yakit'] > 0 else 0,
            'toplam_km': analysis_result.get('toplam_kilometre', 0)
        }

        genel_ozet = {
            'toplam_arac': len(arac_detaylari),
            'toplam_yakit': analysis_result['toplam_yakit'],
            'arac_tipi': 'Kargo Araçları'
        }

        from datetime import datetime
        return render_template('result.html',
                             tahminler=tahminler,
                             plakalar=plakalar,
                             sefer=analysis_result['toplam_sefer'],
                             yakit=f"{analysis_result['toplam_yakit']:.1f}",
                             rolanti=f"{analysis_result['ortalama_yakit_sefer'] * 0.6:.1f}",
                             egim="5.2",
                             ortalama_tahmin=f"{sum(tahminler)/len(tahminler):.2f}" if tahminler else "0",
                             insights=insights,
                             arac_detaylari=arac_detaylari,
                             genel_ozet=genel_ozet,
                             now=datetime.now())

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Upload hatası: {error_detail}")
        flash(f'Hata: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/muhasebe-analyze', methods=['POST'])
def muhasebe_analyze():
    """Muhasebe analizi"""
    try:
        from database import get_muhasebe_data

        baslangic_tarihi = request.form.get('baslangic_tarihi') or None
        bitis_tarihi = request.form.get('bitis_tarihi') or None
        plaka = request.form.get('plaka', '').strip()

        # Dinamik Ayarları Al
        hedef_gelir = request.form.get('hedef_gelir', 1000000)
        hedef_gider = request.form.get('hedef_gider', 750000)
        motorin_fiyat = request.form.get('motorin_fiyat', '').strip()
        adblue_fiyat = request.form.get('adblue_fiyat', '').strip()
        cari_fiyatlar_text = request.form.get('cari_fiyatlar', '').strip()
        harici_gizle = request.form.get('harici_gizle') == 'on'  # Checkbox boolean

        cari_fiyatlar_dict = {}
        if cari_fiyatlar_text:
            for line in cari_fiyatlar_text.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    try:
                        cari_fiyatlar_dict[k.strip()] = float(v.strip())
                    except:
                        pass

        settings = {
            'hedef_gelir': float(hedef_gelir) if hedef_gelir else 1000000.0,
            'hedef_gider': float(hedef_gider) if hedef_gider else 750000.0,
            'motorin_fiyat': float(motorin_fiyat) if motorin_fiyat else None,
            'adblue_fiyat': float(adblue_fiyat) if adblue_fiyat else None,
            'cari_fiyatlar': cari_fiyatlar_dict,
            'harici_gizle': harici_gizle
        }

        result = get_muhasebe_data(baslangic_tarihi, bitis_tarihi, plaka or None, settings)

        if result['status'] == 'error':
            flash(f'❌ Hata: {result["message"]}', 'error')
            return redirect(url_for('muhasebe'))

        return render_template('muhasebe_result.html',
                             baslangic_tarihi=baslangic_tarihi or 'Başlangıç',
                             bitis_tarihi=bitis_tarihi or 'Bugün',
                             plaka=plaka or 'Tümü',
                             hedef_gelir=settings['hedef_gelir'],
                             hedef_gider=settings['hedef_gider'],
                             toplam_gelir=result['toplam_gelir'],
                             toplam_gider=result['toplam_gider'],
                             toplam_yakit_gider=result.get('toplam_yakit_gider', 0),
                             toplam_bakim_gider=result.get('toplam_bakim_gider', 0),
                             toplam_ceza_gider=result.get('toplam_ceza_gider', 0),
                             toplam_hasar_gider=result.get('toplam_hasar_gider', 0),
                             net_kar=result['net_kar'],
                             kar_marji=result['kar_marji'],
                             plaka_bazli=result['plaka_bazli'],
                             aylik_trend=result.get('aylik_trend', {}),
                             cari_bazli=result.get('cari_bazli', []))

    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return redirect(url_for('muhasebe'))

@app.route('/database-status')
def database_status():
    """Veritabanı durumunu görsel olarak göster"""
    from database import get_database_info, get_statistics
    db_info = get_database_info()

    stats = {}
    if db_info.get('exists'):
        try:
            stats = get_statistics()
        except Exception as e:
            stats = {'error': str(e)}

    return render_template('database_status.html', db_info=db_info, stats=stats)

@app.route('/debug-info')
def debug_info():
    """Debug bilgisi JSON formatında"""
    from database import get_database_info, get_statistics
    db_info = get_database_info()

    stats = {}
    if db_info.get('exists'):
        try:
            stats = get_statistics()
        except Exception as e:
            stats = {'error': str(e)}

    return jsonify({
        'database': db_info,
        'statistics': stats
    })

@app.route('/ai-analysis')
def ai_analysis():
    """AI analiz sayfası"""
    from database import get_aktif_kargo_araclari
    plakalar = get_aktif_kargo_araclari()
    return render_template('ai_analysis.html', plakalar=plakalar)

@app.route('/ai-train', methods=['POST'])
def ai_train():
    """AI modellerini eğit"""
    try:
        from ai_model import YakitTahminModeli, AnomalTespitModeli

        # Yakıt tahmin modelini eğit
        tahmin_model = YakitTahminModeli()
        tahmin_result = tahmin_model.egit()

        # Anomali tespit modelini eğit
        anomali_model = AnomalTespitModeli()
        anomali_result = anomali_model.egit()

        if tahmin_result['status'] == 'success' and anomali_result['status'] == 'success':
            flash('✅ AI modelleri başarıyla eğitildi!', 'success')
            return jsonify({
                'status': 'success',
                'tahmin_model': tahmin_result,
                'anomali_model': anomali_result
            })
        else:
            error_msg = tahmin_result.get('message', '') or anomali_result.get('message', '')
            flash(f'❌ Model eğitimi hatası: {error_msg}', 'error')
            return jsonify({
                'status': 'error',
                'message': error_msg
            })
    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/ai-predict', methods=['POST'])
def ai_predict():
    """Yakıt tüketim tahmini yap"""
    try:
        from ai_model import YakitTahminModeli

        plaka = request.form.get('plaka')
        tarih = request.form.get('tarih')
        tahmin_tipi = request.form.get('tahmin_tipi', 'tek')

        model = YakitTahminModeli()

        if tahmin_tipi == 'gelecek_ay':
            result = model.gelecek_ay_tahmini(plaka)
        else:
            result = model.tahmin_yap(plaka, tarih)

        if result['status'] == 'success':
            return render_template('ai_predict_result.html', result=result, tahmin_tipi=tahmin_tipi)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('ai_analysis'))

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('ai_analysis'))

@app.route('/ai-anomaly', methods=['POST', 'GET'])
def ai_anomaly():
    """Anomali tespiti yap"""
    try:
        from ai_model import AnomalTespitModeli

        model = AnomalTespitModeli()
        result = model.anomali_tespit()

        if result['status'] == 'success':
            return render_template('ai_anomaly_result.html', result=result)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('ai_analysis'))

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('ai_analysis'))

@app.route('/anomaly-dashboard')
def anomaly_dashboard():
    """Anomali dashboard sayfası - filtreleme ve grafiklerle"""
    try:
        from ai_model import AnomalTespitModeli
        from database import get_all_plakas

        model = AnomalTespitModeli()
        result = model.anomali_tespit_detayli()

        if result['status'] == 'success':
            plakalar = get_all_plakas()
            return render_template('anomaly_dashboard.html',
                                 result=result,
                                 plakalar=plakalar)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('ai_analysis'))
    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('ai_analysis'))

@app.route('/ai-bulk-predict', methods=['POST'])
def ai_bulk_predict():
    """Tüm plakalar için toplu tahmin"""
    try:
        from ai_model import tum_plakalar_tahmini

        result = tum_plakalar_tahmini()

        if result['status'] == 'success':
            return render_template('ai_bulk_result.html', result=result)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('ai_analysis'))

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('ai_analysis'))

@app.route('/performans-analizi')
def performans_analizi():
    """Performans analizi sayfası"""
    from database import get_all_plakas
    plakalar = get_all_plakas()
    return render_template('performans_analizi.html', plakalar=plakalar)

@app.route('/performans-karsilastirma', methods=['POST'])
def performans_karsilastirma():
    """Tüm araçların performans karşılaştırması"""
    try:
        from ai_model import PerformansAnalizi

        ana_malzeme = request.form.get('ana_malzeme', '').strip()
        arac_tipi = request.form.get('arac_tipi', '').strip()

        analiz = PerformansAnalizi()
        result = analiz.plaka_performans_karsilastirma(
            ana_malzeme_filtre=ana_malzeme if ana_malzeme else None,
            arac_tipi_filtre=arac_tipi if arac_tipi else None
        )

        if result['status'] == 'success':
            return render_template('performans_karsilastirma.html', result=result, selected_malzeme=ana_malzeme, selected_arac_tipi=arac_tipi)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('performans_analizi'))

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('performans_analizi'))

@app.route('/performans-detay', methods=['POST'])
def performans_detay():
    """Belirli bir araç için detaylı performans analizi"""
    try:
        from ai_model import PerformansAnalizi

        plaka = request.form.get('plaka')
        baslangic_tarihi = request.form.get('baslangic_tarihi') or None
        bitis_tarihi = request.form.get('bitis_tarihi') or None

        analiz = PerformansAnalizi()
        result = analiz.plaka_detay_analiz(plaka, baslangic_tarihi, bitis_tarihi)

        if result['status'] == 'success':
            return render_template('performans_detay.html', result=result)
        else:
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('performans_analizi'))

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('performans_analizi'))

@app.route('/performans-export-pdf', methods=['POST'])
def performans_export_pdf():
    """Performans karşılaştırma PDF export"""
    try:
        from ai_model import PerformansAnalizi
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io

        ana_malzeme = request.form.get('ana_malzeme', '').strip()

        analiz = PerformansAnalizi()
        result = analiz.plaka_performans_karsilastirma(ana_malzeme_filtre=ana_malzeme if ana_malzeme else None)

        if result['status'] != 'success':
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('performans_analizi'))

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=1
        )

        malzeme_text = f" - {ana_malzeme}" if ana_malzeme else ""
        title = Paragraph(f"Araç Performans Karşılaştırması{malzeme_text}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))

        ozet_data = [
            ['Metrik', 'Değer'],
            ['Ortalama KM/Litre', f"{tr_format(result['ortalama_km_litre'])} km/L"],
            ['Ortalama Verimlilik', f"{tr_format(result['ortalama_ton_yakit'])} Yük/L"],
            ['Toplam Araç Sayısı', str(result['toplam_arac'])]
        ]

        ozet_table = Table(ozet_data, colWidths=[8*cm, 8*cm])
        ozet_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(ozet_table)
        elements.append(Spacer(1, 1*cm))

        table_data = [['Plaka', 'Ana Malzeme', 'Top. Yakıt(L)', 'Toplam KM', 'Taşıma Miktarı', 'KM/Litre', 'KM/Maliyet', 'Verimlilik']]

        for arac in result['veriler']:
            table_data.append([
                arac['plaka'],
                arac['ana_malzeme'] if arac['ana_malzeme'] else 'Bilinmiyor',
                tr_format(arac['toplam_yakit'], 1),
                tr_format(arac['toplam_km'], 0, True),
                f"{tr_format(arac['toplam_tonaj'], 1)} {arac.get('kantar_birimi', '-')}",
                tr_format(arac['km_litre'], 2),
                f"{tr_format(arac['km_maliyet'], 2)} TL" if arac['km_maliyet'] else 'N/A',
                tr_format(arac['ton_yakit'], 2),
                arac['verimlilik']
            ])

        data_table = Table(table_data, colWidths=[2.8*cm, 3*cm, 2.5*cm, 2.5*cm, 3.5*cm, 2.3*cm, 2.5*cm, 2.3*cm, 2.3*cm])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        elements.append(data_table)

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'performans_raporu_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )

    except Exception as e:
        flash(f'❌ PDF oluşturulamadı: {str(e)}', 'error')
        return redirect(url_for('performans_analizi'))

@app.route('/performans-export-excel', methods=['POST'])
def performans_export_excel():
    """Performans karşılaştırma Excel export"""
    try:
        from ai_model import PerformansAnalizi
        import pandas as pd
        import io

        ana_malzeme = request.form.get('ana_malzeme', '').strip()

        analiz = PerformansAnalizi()
        result = analiz.plaka_performans_karsilastirma(ana_malzeme_filtre=ana_malzeme if ana_malzeme else None)

        if result['status'] != 'success':
            flash(f'❌ {result["message"]}', 'error')
            return redirect(url_for('performans_analizi'))

        df_data = []
        for arac in result['veriler']:
            # Excel için birim eklemesi (Görsel kafa karışıklığını önlemek için)
            birim = arac.get('kantar_birimi', '-')
            df_data.append({
                'Plaka': arac['plaka'],
                'Ana Malzeme': arac['ana_malzeme'] if arac['ana_malzeme'] else 'Bilinmiyor',
                'Toplam Yakıt (L)': arac['toplam_yakit'],
                'Toplam KM': arac['toplam_km'],
                'Taşıma Miktarı': arac['toplam_tonaj'],
                'Birim': birim,
                'KM/Litre': arac['km_litre'] if arac['km_litre'] else 'N/A',
                'KM/Maliyet (TL)': arac['km_maliyet'] if arac['km_maliyet'] else 'N/A',
                'Verimlilik (Yük/L)': arac['ton_yakit'] if arac['ton_yakit'] else 'N/A',
                'Performans Durumu': arac['verimlilik']
            })

        df = pd.DataFrame(df_data)

        ozet_df = pd.DataFrame({
            'Metrik': ['Ortalama KM/Litre', 'Ortalama Verimlilik', 'Toplam Araç Sayısı'],
            'Değer': [
                tr_format(result['ortalama_km_litre']),
                tr_format(result['ortalama_ton_yakit']),
                str(result['toplam_arac'])
            ]
        })

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            ozet_df.to_excel(writer, sheet_name='Özet', index=False)
            df.to_excel(writer, sheet_name='Detaylı Veri', index=False)

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'performans_raporu_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    except Exception as e:
        flash(f'❌ Excel oluşturulamadı: {str(e)}', 'error')
        return redirect(url_for('performans_analizi'))

@app.route('/arac-yonetimi')
def arac_yonetimi():
    """Araç yönetimi sayfası"""
    from database import get_all_araclar

    araclar = get_all_araclar()

    kargo_sayisi = len([a for a in araclar if a['arac_tipi'] == 'KARGO ARACI' and a['aktif'] == 1])
    is_makinesi_sayisi = len([a for a in araclar if a['arac_tipi'] == 'İŞ MAKİNESİ'])
    binek_sayisi = len([a for a in araclar if a['arac_tipi'] == 'BİNEK ARAÇ'])

    return render_template('arac_yonetimi.html',
                         araclar=araclar,
                         kargo_sayisi=kargo_sayisi,
                         is_makinesi_sayisi=is_makinesi_sayisi,
                         binek_sayisi=binek_sayisi)

@app.route('/arac-ekle', methods=['POST'])
def arac_ekle():
    """Yeni araç ekle"""
    try:
        from database import add_arac

        plaka = request.form.get('plaka', '').strip().upper()
        sahip = request.form.get('sahip')
        arac_tipi = request.form.get('arac_tipi')
        notlar = request.form.get('notlar', '').strip()
        varsayilan_malzeme = request.form.get('varsayilan_malzeme', '').strip() or None

        result = add_arac(plaka, sahip, arac_tipi, notlar, varsayilan_malzeme)

        if result['status'] == 'success':
            flash(f'✅ {plaka} plakası başarıyla eklendi!', 'success')
        else:
            flash(f'❌ {result["message"]}', 'error')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-guncelle', methods=['POST'])
def arac_guncelle():
    """Araç güncelle"""
    try:
        from database import update_arac

        plaka = request.form.get('plaka')
        sahip = request.form.get('sahip')
        arac_tipi = request.form.get('arac_tipi')
        aktif = int(request.form.get('aktif', 1))
        notlar = request.form.get('notlar', '').strip()
        varsayilan_malzeme = request.form.get('varsayilan_malzeme', '').strip() or None

        result = update_arac(plaka, sahip, arac_tipi, aktif, notlar, varsayilan_malzeme)

        if result['status'] == 'success':
            flash(f'✅ {plaka} başarıyla güncellendi!', 'success')
        else:
            flash(f'❌ {result["message"]}', 'error')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-sil', methods=['POST'])
def arac_sil():
    """Araç sil"""
    try:
        from database import delete_arac

        plaka = request.form.get('plaka')
        result = delete_arac(plaka)

        if result['status'] == 'success':
            flash(f'✅ {plaka} silindi!', 'success')
        else:
            flash(f'❌ {result["message"]}', 'error')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-toplu-sil', methods=['POST'])
def arac_toplu_sil():
    """Toplu araç sil"""
    try:
        from database import delete_arac

        plakalar = request.form.getlist('plakalar')

        if not plakalar:
            flash('❌ Silinecek araç seçilmedi!', 'error')
            return redirect(url_for('arac_yonetimi'))

        basarili = 0
        basarisiz = 0

        for plaka in plakalar:
            result = delete_arac(plaka)
            if result['status'] == 'success':
                basarili += 1
            else:
                basarisiz += 1

        if basarili > 0:
            flash(f'✅ {basarili} araç başarıyla silindi!', 'success')
        if basarisiz > 0:
            flash(f'⚠️ {basarisiz} araç silinemedi!', 'error')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-toplu-sahip', methods=['POST'])
def arac_toplu_sahip():
    """Toplu araç sahip güncelle (BİZİM/TAŞERON)"""
    try:
        from database import get_db_connection

        plakalar = request.form.getlist('plakalar')
        sahip = request.form.get('sahip')

        if not plakalar:
            flash('❌ Araç seçilmedi!', 'error')
            return redirect(url_for('arac_yonetimi'))

        conn = get_db_connection()
        cursor = conn.cursor()

        basarili = 0
        for plaka in plakalar:
            cursor.execute('UPDATE araclar SET sahip = ? WHERE plaka = ?', (sahip, plaka))
            basarili += 1

        conn.commit()
        conn.close()

        flash(f'✅ {basarili} araç "{sahip}" olarak güncellendi!', 'success')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-toplu-durum', methods=['POST'])
def arac_toplu_durum():
    """Toplu araç durum güncelle (Aktif/Pasif)"""
    try:
        from database import get_db_connection

        plakalar = request.form.getlist('plakalar')
        aktif = request.form.get('aktif')

        if not plakalar:
            flash('❌ Araç seçilmedi!', 'error')
            return redirect(url_for('arac_yonetimi'))

        conn = get_db_connection()
        cursor = conn.cursor()

        basarili = 0
        for plaka in plakalar:
            cursor.execute('UPDATE araclar SET aktif = ? WHERE plaka = ?', (aktif, plaka))
            basarili += 1

        conn.commit()
        conn.close()

        durum_text = 'AKTİF' if aktif == '1' else 'PASİF'
        flash(f'✅ {basarili} araç "{durum_text}" yapıldı!', 'success')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/arac-toplu-import', methods=['POST'])
def arac_toplu_import():
    """Veritabanındaki tüm plakaları araçlar tablosuna ekle - HIZLI VERSİYON"""
    try:
        from database import bulk_import_araclar

        result = bulk_import_araclar()

        if result['status'] == 'success':
            flash(f'✅ {result["eklenen"]} yeni plaka eklendi. Toplam: {result["toplam"]} araç.', 'success')
        else:
            flash(f'❌ Hata: {result["message"]}', 'error')

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('arac_yonetimi'))

@app.route('/export-excel', methods=['POST'])
def export_excel():
    """Analiz sonuçlarını Excel'e dönüştür"""
    try:
        data = request.get_json()
        arac_detaylari = data.get('arac_detaylari', [])

        if not arac_detaylari:
            return jsonify({'status': 'error', 'message': 'Veri bulunamadı'}), 400

        df = pd.DataFrame(arac_detaylari)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Analiz Sonuçları', index=False)

            workbook = writer.book
            worksheet = writer.sheets['Analiz Sonuçları']

            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4CAF50',
                'font_color': 'white',
                'border': 1
            })

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'yakit_analizi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/export-pdf', methods=['POST'])
def export_pdf():
    """Analiz sonuçlarını PDF'e dönüştür"""
    try:
        data = request.get_json()
        arac_detaylari = data.get('arac_detaylari', [])

        if not arac_detaylari:
            return jsonify({'status': 'error', 'message': 'Veri bulunamadı'}), 400

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
        )

        elements.append(Paragraph('Yakıt Analiz Raporu', title_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', styles['Normal']))
        elements.append(Spacer(1, 1*cm))

        verimli_araclar = sorted([a for a in arac_detaylari if a.get('kg_litre_orani')],
                                 key=lambda x: x['kg_litre_orani'], reverse=True)[:5]
        verimsiz_araclar = sorted([a for a in arac_detaylari if a.get('kg_litre_orani')],
                                  key=lambda x: x['kg_litre_orani'])[:5]

        if verimli_araclar:
            elements.append(Paragraph('En Verimli Araçlar (Top 5)', styles['Heading2']))
            verimli_data = [['Plaka', 'Toplam Yakıt (L)', 'KG/Litre']]
            for arac in verimli_araclar:
                verimli_data.append([
                    arac['plaka'],
                    f"{arac.get('toplam_yakit', 0):.2f}",
                    f"{arac.get('kg_litre_orani', 0):.0f}"
                ])

            verimli_table = Table(verimli_data)
            verimli_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(verimli_table)
            elements.append(Spacer(1, 1*cm))

        if verimsiz_araclar:
            elements.append(Paragraph('En Verimsiz Araçlar (Top 5)', styles['Heading2']))
            verimsiz_data = [['Plaka', 'Toplam Yakıt (L)', 'KG/Litre']]
            for arac in verimsiz_araclar:
                verimsiz_data.append([
                    arac['plaka'],
                    f"{arac.get('toplam_yakit', 0):.2f}",
                    f"{arac.get('kg_litre_orani', 0):.0f}"
                ])

            verimsiz_table = Table(verimsiz_data)
            verimsiz_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(verimsiz_table)

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'yakit_analizi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )

    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/kargo-arac-filtre')
def kargo_arac_filtre():
    """Kargo araç filtre sayfası"""
    return render_template('kargo_arac_filtre.html')

@app.route('/binek-arac-filtre')
def binek_arac_filtre():
    """Binek araç filtre sayfası"""
    return render_template('binek_arac_filtre.html')

@app.route('/is-makinesi-filtre')
def is_makinesi_filtre():
    """İş makinesi filtre sayfası"""
    return render_template('is_makinesi_filtre.html')

@app.route('/ai-assistant')
def ai_assistant():
    """AI Asistan sayfası"""
    return render_template('ai_assistant.html')

@app.route('/api/assistant/status')
def assistant_status():
    """Ollama servis durumunu kontrol et"""
    try:
        from gemini_assistant import GeminiAssistant
        assistant = GeminiAssistant()
        status = assistant.check_gemini_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/assistant/ask', methods=['POST'])
def assistant_ask():
    """Asistana soru sor"""
    try:
        from gemini_assistant import GeminiAssistant

        data = request.get_json()
        question = data.get('question', '')

        if not question:
            return jsonify({'status': 'error', 'message': 'Soru boş olamaz'})

        assistant = GeminiAssistant()
        result = assistant.ask_with_db_query(question)

        # Excel veya PDF export varsa session'a kaydet
        if result.get('export_type') in ['excel', 'pdf']:
            import base64
            session['export_file'] = base64.b64encode(result['file_data']).decode('utf-8')
            session['export_type'] = result['export_type']
            session['export_filename'] = result['filename']
            result['download_url'] = '/api/assistant/download'

        return jsonify(result)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/assistant/download')
def assistant_download():
    """Export dosyasını indir"""
    try:
        import base64

        if 'export_file' not in session:
            return jsonify({'status': 'error', 'message': 'İndirilecek dosya bulunamadı'})

        file_data = base64.b64decode(session['export_file'])
        export_type = session.get('export_type', 'excel')
        filename = session.get('export_filename', 'rapor.xlsx')

        # Session'ı temizle
        session.pop('export_file', None)
        session.pop('export_type', None)
        session.pop('export_filename', None)

        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if export_type == 'excel' else 'application/pdf'

        return send_file(
            io.BytesIO(file_data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/assistant/history')
def assistant_history():
    """Sohbet geçmişini getir"""
    try:
        from gemini_assistant import GeminiAssistant
        assistant = GeminiAssistant()
        history = assistant.get_chat_history()
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/assistant/clear', methods=['POST'])
def assistant_clear():
    """Sohbet geçmişini temizle"""
    try:
        from gemini_assistant import GeminiAssistant
        assistant = GeminiAssistant()
        result = assistant.clear_history()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/binek-arac-analizi', methods=['GET', 'POST'])
def binek_arac_analizi():
    """Binek araç analizi sayfası"""
    try:
        from database import get_aktif_binek_araclar, get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Filtreleri al
        baslangic_tarihi = request.form.get('baslangic_tarihi') if request.method == 'POST' else None
        bitis_tarihi = request.form.get('bitis_tarihi') if request.method == 'POST' else None
        plaka_filtre = request.form.get('plaka') if request.method == 'POST' else None
        dahil_taseron = request.form.get('dahil_taseron') == '1' if request.method == 'POST' else False

        aktif_binek = get_aktif_binek_araclar(dahil_taseron=dahil_taseron)

        if not aktif_binek:
            flash('⚠️ Aktif binek araç bulunamadı. Araç Yönetimi\'nden binek araç ekleyin.', 'warning')
            return render_template('result.html',
                                 arac_detaylari=[],
                                 genel_ozet={'arac_tipi': 'Binek Araç', 'toplam_arac': 0, 'toplam_yakit': 0})

        # SQL sorgusu filtrelerle
        where_conditions = [f'y.plaka IN ({",".join("?" * len(aktif_binek))})']
        params = list(aktif_binek)

        if baslangic_tarihi:
            where_conditions.append('y.islem_tarihi >= ?')
            params.append(baslangic_tarihi)

        if bitis_tarihi:
            where_conditions.append('y.islem_tarihi <= ?')
            params.append(bitis_tarihi)

        if plaka_filtre:
            where_conditions.append('y.plaka = ?')
            params.append(plaka_filtre)

        where_clause = ' AND '.join(where_conditions)

        cursor.execute(f'''
            SELECT
                y.plaka,
                SUM(y.yakit_miktari) as toplam_yakit,
                SUM(y.km_bilgisi) as toplam_km,
                AVG(y.yakit_miktari) as ortalama_yakit,
                COUNT(*) as yakit_alimlari
            FROM yakit y
            WHERE {where_clause}
            AND y.yakit_miktari IS NOT NULL
            AND y.yakit_miktari > 0
            GROUP BY y.plaka
            ORDER BY toplam_yakit DESC
        ''', tuple(params))

        rows = cursor.fetchall()

        arac_detaylari = []
        toplam_yakit_genel = 0
        toplam_km_genel = 0

        for row in rows:
            plaka = row['plaka']
            toplam_yakit = float(row['toplam_yakit'])
            yakit_alimlari = row['yakit_alimlari']
            
            # KM Hesabı (Aykırı değerleri/typolar eler: Sadece 0-2000 km arası farkları topla)
            km_query = """
                SELECT SUM(km_fark) as toplam 
                FROM yakit 
                WHERE plaka = ? 
                AND km_fark > 0 AND km_fark < 2000
            """
            km_params = [plaka]
            if baslangic_tarihi:
                km_query += " AND islem_tarihi >= ?"
                km_params.append(baslangic_tarihi)
            if bitis_tarihi:
                km_query += " AND islem_tarihi <= ?"
                km_params.append(bitis_tarihi)
            
            cursor.execute(km_query, km_params)
            km_row = cursor.fetchone()
            toplam_km = float(km_row['toplam'] or 0)
            
            # Eğer km_fark verisi yoksa (Eski sistem/Manuel giriş) MAX-MIN'e fallback yap ama 0'la
            if toplam_km == 0:
                 cursor.execute('''
                    SELECT (MAX(km_bilgisi) - MIN(km_bilgisi)) as fark 
                    FROM yakit 
                    WHERE plaka = ? AND km_bilgisi > 0
                 ''', (plaka,))
                 toplam_km = float(cursor.fetchone()['fark'] or 0)
                 # Eğer MAX-MIN çok devasaysa (typo varsa) 0 kabul et
                 if toplam_km > 20000: toplam_km = 0 

            tuketim = (toplam_yakit / toplam_km * 100) if toplam_km > 0 else 0

            arac_detaylari.append({
                'plaka': plaka,
                'toplam_yakit': round(toplam_yakit, 2),
                'toplam_km': round(toplam_km, 2),
                'ortalama_yakit': round(float(row['ortalama_yakit']), 2),
                'yakit_alimlari': yakit_alimlari,
                'tuketim_100km': round(tuketim, 2)
            })

            toplam_yakit_genel += toplam_yakit
            toplam_km_genel += toplam_km

        genel_ozet = {
            'toplam_arac': len(arac_detaylari),
            'toplam_yakit': toplam_yakit_genel,
            'arac_tipi': 'Binek Araç'
        }

        conn.close()
        plakalar = [arac['plaka'] for arac in arac_detaylari]
        tahminler = [arac['ortalama_yakit'] for arac in arac_detaylari]

        return render_template('result.html',
                             arac_detaylari=arac_detaylari,
                             genel_ozet=genel_ozet,
                             analiz_tipi='binek',
                             sefer=sum(a['yakit_alimlari'] for a in arac_detaylari),
                             yakit=toplam_yakit_genel,
                             toplam_km=toplam_km_genel,
                             ortalama_tahmin=round((toplam_yakit_genel / toplam_km_genel * 100), 2) if toplam_km_genel > 0 else 0,
                             plakalar=plakalar,
                             tahminler=tahminler)

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/is-makinesi-analizi', methods=['GET', 'POST'])
def is_makinesi_analizi():
    """İş makinesi analizi sayfası"""
    try:
        from database import get_aktif_is_makineleri, get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Filtreleri al
        baslangic_tarihi = request.form.get('baslangic_tarihi') if request.method == 'POST' else None
        bitis_tarihi = request.form.get('bitis_tarihi') if request.method == 'POST' else None
        plaka_filtre = request.form.get('plaka') if request.method == 'POST' else None
        dahil_taseron = request.form.get('dahil_taseron') == '1' if request.method == 'POST' else False

        aktif_makineler = get_aktif_is_makineleri(dahil_taseron=dahil_taseron)

        if not aktif_makineler:
            flash('⚠️ Aktif iş makinesi bulunamadı. Araç Yönetimi\'nden iş makinesi ekleyin.', 'warning')
            return render_template('result.html',
                                 arac_detaylari=[],
                                 genel_ozet={'arac_tipi': 'İş Makinesi', 'toplam_arac': 0, 'toplam_yakit': 0})

        # SQL sorgusu filtrelerle
        where_conditions = [f'y.plaka IN ({",".join("?" * len(aktif_makineler))})']
        params = list(aktif_makineler)

        if baslangic_tarihi:
            where_conditions.append('y.islem_tarihi >= ?')
            params.append(baslangic_tarihi)

        if bitis_tarihi:
            where_conditions.append('y.islem_tarihi <= ?')
            params.append(bitis_tarihi)

        if plaka_filtre:
            where_conditions.append('y.plaka = ?')
            params.append(plaka_filtre)

        where_clause = ' AND '.join(where_conditions)

        cursor.execute(f'''
            SELECT
                y.plaka,
                SUM(y.yakit_miktari) as toplam_yakit,
                SUM(y.km_bilgisi) as toplam_km,
                AVG(y.yakit_miktari) as ortalama_yakit,
                COUNT(*) as yakit_alimlari
            FROM yakit y
            WHERE {where_clause}
            AND y.yakit_miktari IS NOT NULL
            AND y.yakit_miktari > 0
            GROUP BY y.plaka
            ORDER BY toplam_yakit DESC
        ''', tuple(params))

        rows = cursor.fetchall()

        arac_detaylari = []
        toplam_yakit_genel = 0
        toplam_km_genel = 0

        for row in rows:
            plaka = row['plaka']
            toplam_yakit = float(row['toplam_yakit'])
            yakit_alimlari = row['yakit_alimlari']
            
            # KM/Saat Hesabı (Aykırı değerleri eler: Sadece 0-500 saat/km arası farkları topla)
            km_query = """
                SELECT SUM(km_fark) as toplam 
                FROM yakit 
                WHERE plaka = ? 
                AND km_fark > 0 AND km_fark < 1000
            """
            km_params = [plaka]
            if baslangic_tarihi:
                km_query += " AND islem_tarihi >= ?"
                km_params.append(baslangic_tarihi)
            if bitis_tarihi:
                km_query += " AND islem_tarihi <= ?"
                km_params.append(bitis_tarihi)
            
            cursor.execute(km_query, km_params)
            km_row = cursor.fetchone()
            toplam_km = float(km_row['toplam'] or 0)
            
            # Fallback
            if toplam_km == 0:
                 cursor.execute('''
                    SELECT (MAX(km_bilgisi) - MIN(km_bilgisi)) as fark 
                    FROM yakit 
                    WHERE plaka = ? AND km_bilgisi > 0
                 ''', (plaka,))
                 toplam_km = float(cursor.fetchone()['fark'] or 0)
                 if toplam_km > 10000: toplam_km = 0

            # İş makinesinde tüketim L/Saat olduğu için *100 kullanılmaz
            tuketim = (toplam_yakit / toplam_km) if toplam_km > 0 else 0

            arac_detaylari.append({
                'plaka': plaka,
                'toplam_yakit': round(toplam_yakit, 2),
                'toplam_km': round(toplam_km, 2),
                'ortalama_yakit': round(float(row['ortalama_yakit']), 2),
                'yakit_alimlari': yakit_alimlari,
                'tuketim_100km': round(tuketim, 2)
            })

            toplam_yakit_genel += toplam_yakit
            toplam_km_genel += toplam_km

        genel_ozet = {
            'toplam_arac': len(arac_detaylari),
            'toplam_yakit': toplam_yakit_genel,
            'arac_tipi': 'İş Makinesi'
        }

        conn.close()
        plakalar = [arac['plaka'] for arac in arac_detaylari]
        tahminler = [arac['ortalama_yakit'] for arac in arac_detaylari]

        return render_template('result.html',
                             arac_detaylari=arac_detaylari,
                             genel_ozet=genel_ozet,
                             analiz_tipi='is_makinesi',
                             sefer=sum(a['yakit_alimlari'] for a in arac_detaylari),
                             yakit=toplam_yakit_genel,
                             toplam_km=toplam_km_genel,
                             ortalama_tahmin=round(toplam_yakit_genel / toplam_km_genel, 2) if toplam_km_genel > 0 else 0,
                             plakalar=plakalar,
                             tahminler=tahminler)

    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')
        return redirect(url_for('index'))


# -------------------------------------------------------------------------
# ARA�!  BAKIM MOD�SL�S ROTALARI
# -------------------------------------------------------------------------

@app.route('/bakim')
def bakim_sayfasi():
    """Araç bakım sayfası"""
    from database import get_bakim_kayitlari, get_all_plakas
    from datetime import date
    
    selected_plaka = request.args.get('plaka')
    
    kayitlar = get_bakim_kayitlari(selected_plaka if selected_plaka else None)
    plakalar = get_all_plakas()
    
    # İstatistikler
    toplam_maliyet = sum(float(k['maliyet'] or 0) for k in kayitlar)
    toplam_kayit = len(kayitlar)
    son_islem_tarihi = kayitlar[0]['tarih'] if kayitlar else '-'
    
    istatistik = {
        'toplam_maliyet': toplam_maliyet,
        'toplam_kayit': toplam_kayit,
        'son_islem_tarihi': son_islem_tarihi
    }

    return render_template('bakim.html', 
                         kayitlar=kayitlar, 
                         plakalar=plakalar, 
                         selected_plaka=selected_plaka,
                         today=date.today().strftime('%Y-%m-%d'),
                         istatistik=istatistik)

@app.route('/bakim-ekle', methods=['POST'])
def bakim_ekle():
    """Yeni bakım kaydı ekle"""
    from database import add_bakim_kaydi
    
    data = {
        'plaka': request.form.get('plaka'),
        'bakim_tipi': request.form.get('bakim_tipi'),
        'yapilan_islem': request.form.get('yapilan_islem'),
        'tarih': request.form.get('tarih'),
        'km': request.form.get('km'),
        'maliyet': request.form.get('maliyet'),
        'bir_sonraki_bakim_km': request.form.get('bir_sonraki_bakim_km'),
        'bir_sonraki_bakim_tarih': request.form.get('bir_sonraki_bakim_tarih'),
        
        # Yeni Alanlar
        'bildiren_kisi': request.form.get('bildiren_kisi'),
        'iletisim_tel': request.form.get('iletisim_tel'),
        'ariza_saati': request.form.get('ariza_saati'),
        'ariza_konumu': request.form.get('ariza_konumu'),
        'operasyon_durumu': request.form.get('operasyon_durumu'),
        'servis_adi': request.form.get('servis_adi'),
        'servis_giris_tarihi': request.form.get('servis_giris_tarihi'),
        'servis_cikis_tarihi': request.form.get('servis_cikis_tarihi'),
        'iscilik_maliyeti': request.form.get('iscilik_maliyeti'),
        'parca_maliyeti': request.form.get('parca_maliyeti'),
        'fatura_no': request.form.get('fatura_no'),
        'garanti_durumu': request.form.get('garanti_durumu'),
        'durum': request.form.get('durum')
    }
    
    result = add_bakim_kaydi(data)
    
    if result['status'] == 'success':
        flash('✅ Bakım kaydı başarıyla eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
        
    return redirect(url_for('bakim_sayfasi', plaka=data['plaka']))

@app.route('/bakim-guncelle/<int:id>', methods=['POST'])
def bakim_guncelle(id):
    """Mevcut bir bakım kaydını servis ve maliyet bilgileriyle kapat"""
    from database import update_bakim_maliyet
    
    data = {
        'servis_adi': request.form.get('servis_adi'),
        'servis_giris_tarihi': request.form.get('servis_giris_tarihi'),
        'servis_cikis_tarihi': request.form.get('servis_cikis_tarihi'),
        'iscilik_maliyeti': request.form.get('iscilik_maliyeti'),
        'parca_maliyeti': request.form.get('parca_maliyeti'),
        'maliyet': request.form.get('maliyet'),
        'fatura_no': request.form.get('fatura_no'),
        'garanti_durumu': request.form.get('garanti_durumu'),
        'bir_sonraki_bakim_km': request.form.get('bir_sonraki_bakim_km'),
        'bir_sonraki_bakim_tarih': request.form.get('bir_sonraki_bakim_tarih')
    }
    
    result = update_bakim_maliyet(id, data)
    
    if result['status'] == 'success':
        flash('✅ Bakım kaydı başarıyla güncellendi ve kapatıldı.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
        
    return redirect(request.referrer or url_for('bakim_sayfasi'))

@app.route('/bakim-sil/<int:id>', methods=['POST'])
def bakim_sil(id):
    """Bakım kaydı sil"""
    from database import delete_bakim
    
    result = delete_bakim(id)
    
    if result['status'] == 'success':
        flash('�S&  Kayıt silindi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
        
    return redirect(request.referrer or url_for('bakim_sayfasi'))

@app.route('/bakim-analiz')
def bakim_analiz_sayfasi():
    """Araç bakım analiz paneli"""
    from database import get_bakim_analiz_data, get_all_plakas
    import json
    
    analiz_data = get_bakim_analiz_data()
    plakalar = get_all_plakas()
    
    return render_template('bakim_analiz.html', 
                         data=analiz_data,
                         plakalar=plakalar,
                         json_data=json.dumps(analiz_data))


# -------------------------------------------------------------------------
# ŞOFÖR YÖNETİMİ (AŞAMA 2)
# -------------------------------------------------------------------------

@app.route('/soforler')
def soforler_sayfasi():
    """Şoför yönetimi sayfası"""
    from database import get_soforler
    soforler = get_soforler()
    return render_template('soforler.html', soforler=soforler)

@app.route('/sofor-ekle', methods=['POST'])
def view_sofor_ekle():
    """Yeni şoför ekle"""
    from database import add_sofor
    data = {
        'ad_soyad': request.form.get('ad_soyad'),
        'telefon': request.form.get('telefon'),
        'tc_no': request.form.get('tc_no'),
        'aktif': request.form.get('aktif', 1)
    }
    result = add_sofor(data)
    if result['status'] == 'success':
        flash('✅ Şoför başarıyla eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('soforler_sayfasi'))

@app.route('/sofor-guncelle/<int:id>', methods=['POST'])
def view_sofor_guncelle(id):
    """Şoför bilgilerini güncelle"""
    from database import update_sofor
    data = {
        'ad_soyad': request.form.get('ad_soyad'),
        'telefon': request.form.get('telefon'),
        'tc_no': request.form.get('tc_no'),
        'aktif': request.form.get('aktif', 1)
    }
    result = update_sofor(id, data)
    if result['status'] == 'success':
        flash('✅ Şoför başarıyla güncellendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('soforler_sayfasi'))

@app.route('/sofor-sil/<int:id>', methods=['POST'])
def view_sofor_sil(id):
    """Şoför sil"""
    from database import delete_sofor
    result = delete_sofor(id)
    if result['status'] == 'success':
        flash('🗑️ Şoför başarıyla silindi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('soforler_sayfasi'))


# -------------------------------------------------------------------------
# KAZA, CEZA ve HASAR YÖNETİMİ (AŞAMA 3)
# -------------------------------------------------------------------------

@app.route('/hasar-ceza-yonetimi')
def hasar_ceza_sayfasi():
    """Hasar ve Ceza Yönetimi Sayfası"""
    from database import get_cezalar, get_hasarlar, get_soforler, get_all_plakas
    cezalar = get_cezalar()
    hasarlar = get_hasarlar()
    soforler = get_soforler(aktif_sadece=True)
    plakalar = get_all_plakas()
    
    return render_template('hasar_ceza.html', cezalar=cezalar, hasarlar=hasarlar, soforler=soforler, plakalar=plakalar)

@app.route('/ceza-ekle', methods=['POST'])
def view_ceza_ekle():
    from database import add_ceza
    data = {
        'plaka': request.form.get('plaka'),
        'sofor_id': request.form.get('sofor_id') or None,
        'tarih': request.form.get('tarih'),
        'tutar': request.form.get('tutar'),
        'aciklama': request.form.get('aciklama'),
        'odeme_durumu': request.form.get('odeme_durumu', 'Ödenmedi')
    }
    result = add_ceza(data)
    if result['status'] == 'success':
        flash('✅ Ceza başarıyla eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('hasar_ceza_sayfasi'))

@app.route('/ceza-sil/<int:id>', methods=['POST'])
def view_ceza_sil(id):
    from database import delete_ceza
    result = delete_ceza(id)
    if result['status'] == 'success':
        flash('🗑️ Ceza silindi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('hasar_ceza_sayfasi'))

@app.route('/hasar-ekle', methods=['POST'])
def view_hasar_ekle():
    from database import add_hasar
    data = {
        'plaka': request.form.get('plaka'),
        'sofor_id': request.form.get('sofor_id') or None,
        'tarih': request.form.get('tarih'),
        'tutar': request.form.get('tutar'),
        'aciklama': request.form.get('aciklama'),
        'sigorta_karsiladi_mi': request.form.get('sigorta_karsiladi_mi', 0)
    }
    result = add_hasar(data)
    if result['status'] == 'success':
        flash('✅ Hasar kaydı eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('hasar_ceza_sayfasi'))

@app.route('/hasar-sil/<int:id>', methods=['POST'])
def view_hasar_sil(id):
    from database import delete_hasar
    result = delete_hasar(id)
    if result['status'] == 'success':
        flash('🗑️ Hasar kaydı silindi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('hasar_ceza_sayfasi'))


# -------------------------------------------------------------------------
# LASTİK YÖNETİMİ (AŞAMA 4)
# -------------------------------------------------------------------------

@app.route('/lastik-yonetimi')
def lastik_yonetimi_sayfasi():
    """Lastik Yönetimi Sayfası"""
    from database import get_lastikler, get_aktif_kargo_araclari
    lastikler = get_lastikler(aktif_sadece=True)
    plakalar = get_aktif_kargo_araclari()
    return render_template('lastik_yonetimi.html', lastikler=lastikler, plakalar=plakalar)

@app.route('/lastik-ekle', methods=['POST'])
def view_lastik_ekle():
    from database import add_lastik
    data = {
        'marka': request.form.get('marka'),
        'ebat': request.form.get('ebat'),
        'seri_no': request.form.get('seri_no'),
        'fiyat': request.form.get('fiyat'),
        'alinma_tarihi': request.form.get('alinma_tarihi')
    }
    result = add_lastik(data)
    if result['status'] == 'success':
        flash('✅ Lastik envantere eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('lastik_yonetimi_sayfasi'))

@app.route('/lastik-sil/<int:id>', methods=['POST'])
def view_lastik_sil(id):
    from database import delete_lastik
    result = delete_lastik(id)
    if result['status'] == 'success':
        flash('🗑️ Lastik kaydı silindi (pasife çekildi).', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
    return redirect(url_for('lastik_yonetimi_sayfasi'))

@app.route('/api/arac-lastikleri/<plaka>')
def api_arac_lastikleri(plaka):
    from database import get_arac_lastikleri
    lastikler = get_arac_lastikleri(plaka)
    return jsonify({'status': 'success', 'data': lastikler})

@app.route('/api/lastik-tak', methods=['POST'])
def api_lastik_tak():
    try:
        from database import tak_lastik
        plaka = request.form.get('plaka')
        lastik_id = request.form.get('lastik_id')
        pozisyon = request.form.get('pozisyon')
        tarih = request.form.get('takilma_tarihi')
        km = request.form.get('takilma_km')
        
        result = tak_lastik(plaka, lastik_id, pozisyon, tarih, km)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/lastik-sok', methods=['POST'])
def api_lastik_sok():
    try:
        from database import sok_lastik
        durum_id = request.form.get('durum_id')
        tarih = request.form.get('sokulme_tarihi')
        km = request.form.get('sokulme_km')
        
        result = sok_lastik(durum_id, tarih, km)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/upload', methods=['POST'])
def upload_files():
    """Dosyaları yükle ve işle"""
    try:
        if 'motorin_file' not in request.files and 'kantar_file' not in request.files and 'takip_file' not in request.files:
            flash('❌ Hiçbir dosya seçilmedi!', 'error')
            return redirect(url_for('index'))

        upload_folder = os.path.dirname(os.path.abspath(__file__)) # Direct to root where excel_to_sqlite runs
        
        # Dosyaları kaydet
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        
        # 1. Motorin / Yakıt Dosyası
        if 'motorin_file' in request.files:
            f = request.files['motorin_file']
            if f.filename:
                new_filename = timestamp + f.filename
                filepath = os.path.join(upload_folder, new_filename)
                f.save(filepath)
                saved_files.append(new_filename)

        # 2. Kantar Dosyası
        if 'kantar_file' in request.files:
            f = request.files['kantar_file']
            if f.filename:
                new_filename = timestamp + f.filename
                filepath = os.path.join(upload_folder, new_filename)
                f.save(filepath)
                saved_files.append(new_filename)

        # 3. Araç Takip Dosyası
        if 'takip_file' in request.files:
            f = request.files['takip_file']
            if f.filename:
                new_filename = timestamp + f.filename
                filepath = os.path.join(upload_folder, new_filename)
                f.save(filepath)
                saved_files.append(new_filename)

        if not saved_files:
            flash('⚠️ Dosya seçildi ama isimleri boş olabilir.', 'warning')
            return redirect(url_for('index'))

        # İşlemi başlat
        from excel_to_sqlite import process_excel_files
        
        # Sadece bu klasörü işle (zaten root'a kaydettik)
        result = process_excel_files(custom_directory=upload_folder)
        
        # Sonuçları göster
        success_count = result.get('processed', 0)
        skipped_count = result.get('skipped', 0)
        failed_count = result.get('failed', 0)
        
        msg = f"✅ İşlem Tamamlandı: {success_count} dosya işlendi."
        if skipped_count > 0:
            msg += f" ({skipped_count} dosya atlandı)"
        if failed_count > 0:
            msg += f" ⚠️ {failed_count} dosya hatalı."
            
        flash(msg, 'success' if failed_count == 0 else 'warning')
        
    except Exception as e:
        flash(f'❌ Hata: {str(e)}', 'error')

    return redirect(url_for('index'))


# -------------------------------------------------------------------------
# ŞOFÖR PANELİ (PWA - AŞAMA 5)
# -------------------------------------------------------------------------

@app.route('/sofor-login', methods=['GET', 'POST'])
def sofor_login():
    if request.method == 'POST':
        telefon = request.form.get('telefon')
        from database import get_sofor_by_telefon
        sofor = get_sofor_by_telefon(telefon)
        if sofor:
            session['sofor_id'] = sofor['id']
            session['sofor_adi'] = sofor['ad_soyad']
            return redirect(url_for('sofor_paneli'))
        else:
            flash('Böyle bir telefon numarasına sahip aktif şoför bulunamadı.', 'error')
    return render_template('sofor_login.html')

@app.route('/sofor-logout')
def sofor_logout():
    session.pop('sofor_id', None)
    session.pop('sofor_adi', None)
    return redirect(url_for('sofor_login'))

@app.route('/sofor-paneli')
def sofor_paneli():
    if 'sofor_id' not in session:
        return redirect(url_for('sofor_login'))
    from database import get_aktif_sefer, get_aktif_kargo_araclari
    sofor_id = session['sofor_id']
    aktif_sefer = get_aktif_sefer(sofor_id)
    plakalar = get_aktif_kargo_araclari()
    return render_template('sofor_paneli.html', sofor_adi=session['sofor_adi'], aktif_sefer=aktif_sefer, plakalar=plakalar)

@app.route('/api/sefer-baslat', methods=['POST'])
def api_sefer_baslat():
    if 'sofor_id' not in session:
        return jsonify({'status': 'error', 'message': 'Oturum kapalı'})
    sofor_id = session['sofor_id']
    plaka = request.form.get('plaka')
    km = request.form.get('km')
    from database import baslat_sefer
    return jsonify(baslat_sefer(sofor_id, plaka, km))

@app.route('/api/sefer-bitir', methods=['POST'])
def api_sefer_bitir():
    sefer_id = request.form.get('sefer_id')
    km = request.form.get('km')
    from database import bitir_sefer
    return jsonify(bitir_sefer(sefer_id, km))

import os
from werkzeug.utils import secure_filename
from datetime import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'sofor_bildirim')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/yakit-bildir', methods=['POST'])
def api_yakit_bildir():
    if 'sofor_id' not in session:
        return jsonify({'status': 'error', 'message': 'Oturum kapalı'})
    
    sofor_id = session['sofor_id']
    from database import get_aktif_sefer, add_yakit_from_sofor
    aktif_sefer = get_aktif_sefer(sofor_id)
    
    if not aktif_sefer:
        return jsonify({'status': 'error', 'message': 'Aktif sefer bulunamadı. Önce sefer başlatın.'})
        
    plaka = aktif_sefer['plaka']
    litre = request.form.get('litre')
    file = request.files.get('fotograf')
    
    if not file or not litre:
        return jsonify({'status': 'error', 'message': 'Fotoğraf ve litre bilgisi zorunludur.'})
        
    filename = secure_filename(f"yakit_{plaka}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    db_filepath = f"/static/uploads/sofor_bildirim/{filename}"
    return jsonify(add_yakit_from_sofor(sofor_id, plaka, litre, db_filepath))

@app.route('/api/hasar-bildir', methods=['POST'])
def api_hasar_bildir():
    if 'sofor_id' not in session:
        return jsonify({'status': 'error', 'message': 'Oturum kapalı'})
        
    sofor_id = session['sofor_id']
    from database import get_aktif_sefer, add_hasar
    aktif_sefer = get_aktif_sefer(sofor_id)
    
    if not aktif_sefer:
        return jsonify({'status': 'error', 'message': 'Aktif sefer bulunamadı.'})
        
    plaka = aktif_sefer['plaka']
    aciklama = request.form.get('aciklama')
    enlem = request.form.get('enlem')
    boylam = request.form.get('boylam')
    file = request.files.get('fotograf')
    
    db_filepath = None
    if file:
        filename = secure_filename(f"hasar_{plaka}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        db_filepath = f"/static/uploads/sofor_bildirim/{filename}"
        
    data = {
        'plaka': plaka,
        'sofor_id': sofor_id,
        'tarih': datetime.now().strftime('%Y-%m-%d'),
        'tutar': 0, # Hasar anında tutar belli değil
        'aciklama': aciklama,
        'sigorta_karsiladi_mi': 0,
        'konum_enlem': enlem,
        'konum_boylam': boylam,
        'fotograf_yolu': db_filepath
    }
    
    return jsonify(add_hasar(data))

@app.route('/api/ariza-bildir', methods=['POST'])
def api_ariza_bildir():
    if 'sofor_id' not in session:
        return jsonify({'status': 'error', 'message': 'Oturum kapalı'})
        
    sofor_id = session['sofor_id']
    from database import get_aktif_sefer, add_ariza_from_sofor
    aktif_sefer = get_aktif_sefer(sofor_id)
    
    if not aktif_sefer:
        return jsonify({'status': 'error', 'message': 'Aktif sefer bulunamadı.'})
        
    plaka = aktif_sefer['plaka']
    aciklama = request.form.get('aciklama')
    telefon = request.form.get('telefon')
    
    if not aciklama:
        return jsonify({'status': 'error', 'message': 'Açıklama zorunludur.'})
        
    return jsonify(add_ariza_from_sofor(sofor_id, plaka, aciklama, telefon))

@app.route('/api/evrak-gonder', methods=['POST'])
def api_evrak_gonder():
    if 'sofor_id' not in session:
        return jsonify({'status': 'error', 'message': 'Oturum kapalı'})
        
    sofor_id = session['sofor_id']
    from database import get_aktif_sefer, add_evrak_from_sofor
    aktif_sefer = get_aktif_sefer(sofor_id)
    
    if not aktif_sefer:
        return jsonify({'status': 'error', 'message': 'Aktif sefer bulunamadı. Önce sefer başlatın.'})
        
    plaka = aktif_sefer['plaka']
    evrak_tipi = request.form.get('evrak_tipi')
    aciklama = request.form.get('aciklama')
    file = request.files.get('fotograf')
    
    if not file or not evrak_tipi:
        return jsonify({'status': 'error', 'message': 'Fotoğraf ve evrak tipi zorunludur.'})
        
    filename = secure_filename(f"evrak_{plaka}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    db_filepath = f"/static/uploads/sofor_bildirim/{filename}"
    return jsonify(add_evrak_from_sofor(sofor_id, plaka, evrak_tipi, aciklama, db_filepath))

@app.route('/saha-bildirimleri')
def saha_bildirimleri():
    """Yöneticiler için Saha Bildirim Merkezi"""
    from database import get_saha_bildirimleri
    bildirimler = get_saha_bildirimleri()
    return render_template('saha_bildirimleri.html', bildirimler=bildirimler)

if __name__ == '__main__':
    print("\n" + "="*50)
    print(">> Flask Yakit Tahmin Sistemi Baslatiliyor...")
    print("="*50)
    print(">> URL: http://localhost:5000")
    print(">> Veritabani: kargo_data.db")
    print(">> Durum: http://localhost:5000/database-status")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
