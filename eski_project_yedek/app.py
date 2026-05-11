import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from datetime import datetime

from database import (
    init_db, get_db_stats, get_yakit_data, get_yakit_aylik_ozet,
    get_plaka_listesi, get_plaka_ozet, get_araclar, upsert_arac,
    add_bakim, get_bakim_listesi, get_muhasebe_ozet, get_kargo_verimlilik,
    get_connection
)
from excel_to_sqlite import import_yakit, import_kantar, import_takip
from ollama_assistant import ask_ollama, check_ollama_status, get_quick_insights
from export_utils import export_to_excel, export_to_pdf

app = Flask(__name__)
app.secret_key = 'kargo-analiz-secret-2024'

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

init_db()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    stats = get_db_stats()
    aylik = get_yakit_aylik_ozet()
    insights = get_quick_insights()
    return render_template('index.html', stats=stats, aylik=aylik[:6], insights=insights)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        dosya_turu = request.form.get('dosya_turu', 'yakit')
        file = request.files.get('dosya')

        if not file or file.filename == '':
            flash('Dosya seçilmedi', 'error')
            return redirect(url_for('upload'))

        if not allowed_file(file.filename):
            flash('Geçersiz dosya formatı. Excel (.xlsx, .xls) veya CSV kullanın.', 'error')
            return redirect(url_for('upload'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if dosya_turu == 'yakit':
            result = import_yakit(filepath)
        elif dosya_turu == 'kantar':
            result = import_kantar(filepath)
        elif dosya_turu == 'takip':
            result = import_takip(filepath)
        else:
            result = {'success': False, 'error': 'Geçersiz dosya türü'}

        os.remove(filepath)

        if result['success']:
            flash(f"Başarıyla aktarıldı: {result['inserted']} kayıt eklendi, {result['skipped']} satır atlandı.", 'success')
        else:
            flash(f"Hata: {result.get('error', 'Bilinmeyen hata')}", 'error')

        return redirect(url_for('upload'))

    return render_template('upload.html')


@app.route('/yakit')
def yakit():
    plaka = request.args.get('plaka')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')
    arac_tipi = request.args.get('arac_tipi')

    veriler = get_yakit_data(plaka, baslangic, bitis, arac_tipi)
    plakalar = get_plaka_listesi()
    aylik = get_yakit_aylik_ozet(arac_tipi)

    return render_template('yakit.html',
                           veriler=veriler[:200],
                           plakalar=plakalar,
                           aylik=aylik,
                           filters={'plaka': plaka, 'baslangic': baslangic, 'bitis': bitis, 'arac_tipi': arac_tipi})


@app.route('/api/yakit/chart')
def yakit_chart_data():
    arac_tipi = request.args.get('arac_tipi')
    aylik = get_yakit_aylik_ozet(arac_tipi)

    labels = [a['ay'] for a in reversed(aylik[:12])]
    yakit = [round(a['toplam_yakit'] or 0, 2) for a in reversed(aylik[:12])]
    tutar = [round(a['toplam_tutar'] or 0, 2) for a in reversed(aylik[:12])]

    return jsonify({'labels': labels, 'yakit': yakit, 'tutar': tutar})


@app.route('/analiz')
def analiz():
    arac_tipi = request.args.get('arac_tipi', 'Kargo')
    plakalar = get_plaka_listesi()
    verimlilik = get_kargo_verimlilik()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT y.plaka,
               SUM(y.yakit_miktari) as toplam_yakit,
               SUM(y.satir_tutari) as toplam_maliyet,
               COUNT(*) as islem_sayisi,
               AVG(y.birim_fiyat) as ort_birim_fiyat
        FROM yakit y
        LEFT JOIN araclar a ON y.plaka = a.plaka
        WHERE y.yakit_miktari > 0 AND (a.arac_tipi = ? OR a.arac_tipi IS NULL)
        GROUP BY y.plaka
        ORDER BY toplam_yakit DESC
        LIMIT 20
    ''', (arac_tipi,))
    plaka_analiz = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT strftime('%Y-%m', islem_tarihi) as ay,
               SUM(yakit_miktari) as yakit,
               SUM(satir_tutari) as maliyet
        FROM yakit
        WHERE yakit_miktari > 0
        GROUP BY ay
        ORDER BY ay DESC
        LIMIT 12
    ''')
    trend = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template('analiz.html',
                           plaka_analiz=plaka_analiz,
                           verimlilik=verimlilik[:15],
                           trend=list(reversed(trend)),
                           arac_tipi=arac_tipi,
                           plakalar=plakalar)


@app.route('/muhasebe')
def muhasebe():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT strftime('%Y-%m', islem_tarihi) as ay
        FROM yakit WHERE islem_tarihi IS NOT NULL
        ORDER BY ay DESC
    ''')
    aylar = [r['ay'] for r in cursor.fetchall()]
    conn.close()

    secili_ay = request.args.get('ay', aylar[0] if aylar else None)
    ozet = get_muhasebe_ozet(secili_ay)
    bakim = get_bakim_listesi()

    toplam_bakim = sum(b['maliyet'] or 0 for b in bakim)

    return render_template('muhasebe.html',
                           aylar=aylar,
                           secili_ay=secili_ay,
                           ozet=ozet,
                           bakim=bakim[:20],
                           toplam_bakim=toplam_bakim)


@app.route('/araclar', methods=['GET', 'POST'])
def araclar():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            plaka = request.form.get('plaka')
            sahip = request.form.get('sahip')
            arac_tipi = request.form.get('arac_tipi')
            aktif = 1 if request.form.get('aktif') == '1' else 0
            notlar = request.form.get('notlar', '')
            upsert_arac(plaka, sahip, arac_tipi, aktif, notlar)
            flash(f'{plaka} güncellendi.', 'success')

        elif action == 'bakim':
            plaka = request.form.get('plaka')
            bakim_tipi = request.form.get('bakim_tipi')
            maliyet = float(request.form.get('maliyet', 0))
            tarih = request.form.get('tarih')
            aciklama = request.form.get('aciklama', '')
            add_bakim(plaka, bakim_tipi, maliyet, tarih, aciklama)
            flash(f'{plaka} bakım kaydı eklendi.', 'success')

        return redirect(url_for('araclar'))

    arac_listesi = get_araclar()
    bakim = get_bakim_listesi()
    return render_template('araclar.html', araclar=arac_listesi, bakim=bakim[:30])


@app.route('/araclar/<plaka>')
def arac_detay(plaka):
    ozet = get_plaka_ozet(plaka)
    yakit = get_yakit_data(plaka=plaka)
    bakim = get_bakim_listesi(plaka)
    return render_template('arac_detay.html', plaka=plaka, ozet=ozet, yakit=yakit[:50], bakim=bakim)


@app.route('/asistan')
def asistan():
    status = check_ollama_status()
    insights = get_quick_insights()
    return render_template('asistan.html', ollama_status=status, insights=insights)


@app.route('/api/asistan/chat', methods=['POST'])
def asistan_chat():
    data = request.get_json()
    soru = data.get('soru', '').strip()
    model = data.get('model', None)
    gecmis = data.get('gecmis', [])

    if not soru:
        return jsonify({'success': False, 'answer': 'Soru boş olamaz.'})

    result = ask_ollama(soru, model, gecmis)
    return jsonify(result)


@app.route('/api/ollama/status')
def ollama_status():
    return jsonify(check_ollama_status())


@app.route('/export/excel')
def export_excel():
    tip = request.args.get('tip', 'yakit')
    plaka = request.args.get('plaka')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')

    if tip == 'yakit':
        data = get_yakit_data(plaka, baslangic, bitis)
        columns = [
            {'key': 'plaka', 'header': 'Plaka', 'width': 12},
            {'key': 'islem_tarihi', 'header': 'Tarih', 'width': 12, 'type': 'date'},
            {'key': 'saat', 'header': 'Saat', 'width': 8},
            {'key': 'yakit_miktari', 'header': 'Yakıt (L)', 'width': 12, 'type': 'number'},
            {'key': 'birim_fiyat', 'header': 'Birim Fiyat', 'width': 12, 'type': 'number'},
            {'key': 'satir_tutari', 'header': 'Tutar (₺)', 'width': 14, 'type': 'number'},
            {'key': 'stok_adi', 'header': 'Stok', 'width': 15},
            {'key': 'km_bilgisi', 'header': 'KM', 'width': 10, 'type': 'number'},
        ]
        title = 'Yakıt Tüketim Raporu'
        filename = 'yakit_raporu.xlsx'
    elif tip == 'araclar':
        data = get_araclar()
        columns = [
            {'key': 'plaka', 'header': 'Plaka', 'width': 12},
            {'key': 'sahip', 'header': 'Sahip', 'width': 10},
            {'key': 'arac_tipi', 'header': 'Araç Tipi', 'width': 14},
            {'key': 'toplam_yakit', 'header': 'Toplam Yakıt (L)', 'width': 18, 'type': 'number'},
            {'key': 'toplam_maliyet', 'header': 'Toplam Maliyet (₺)', 'width': 20, 'type': 'number'},
        ]
        title = 'Araç Listesi'
        filename = 'araclar.xlsx'
    else:
        return jsonify({'error': 'Geçersiz tip'}), 400

    output = export_to_excel(data, title, columns)
    return send_file(output, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/export/pdf')
def export_pdf():
    tip = request.args.get('tip', 'yakit')
    plaka = request.args.get('plaka')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')

    if tip == 'yakit':
        data = get_yakit_data(plaka, baslangic, bitis)[:500]
        columns = [
            {'key': 'plaka', 'header': 'Plaka', 'pdf_width': 2.5*72/25.4},
            {'key': 'islem_tarihi', 'header': 'Tarih', 'pdf_width': 2.2*72/25.4},
            {'key': 'yakit_miktari', 'header': 'Yakıt (L)', 'type': 'number', 'pdf_width': 2*72/25.4},
            {'key': 'birim_fiyat', 'header': 'B.Fiyat', 'type': 'number', 'pdf_width': 2*72/25.4},
            {'key': 'satir_tutari', 'header': 'Tutar (₺)', 'type': 'number', 'pdf_width': 2.5*72/25.4},
            {'key': 'stok_adi', 'header': 'Stok', 'pdf_width': 3*72/25.4},
        ]
        title = 'Yakıt Tüketim Raporu'
        filename = 'yakit_raporu.pdf'
    else:
        return jsonify({'error': 'Geçersiz tip'}), 400

    output = export_to_pdf(data, title, columns)
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/veritabani')
def veritabani():
    stats = get_db_stats()
    return render_template('veritabani.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
