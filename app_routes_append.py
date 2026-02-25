
# -------------------------------------------------------------------------
# ARAÇ BAKIM MODÜLÜ ROTALARI
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
        'bir_sonraki_bakim_tarih': request.form.get('bir_sonraki_bakim_tarih')
    }
    
    result = add_bakim_kaydi(data)
    
    if result['status'] == 'success':
        flash('✅ Bakım kaydı başarıyla eklendi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
        
    return redirect(url_for('bakim_sayfasi', plaka=data['plaka']))

@app.route('/bakim-sil/<int:id>', methods=['POST'])
def bakim_sil(id):
    """Bakım kaydı sil"""
    from database import delete_bakim
    
    result = delete_bakim(id)
    
    if result['status'] == 'success':
        flash('✅ Kayıt silindi.', 'success')
    else:
        flash(f'❌ Hata: {result["message"]}', 'error')
        
    return redirect(request.referrer or url_for('bakim_sayfasi'))
