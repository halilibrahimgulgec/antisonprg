import sqlite3
from database import get_db_connection

# Sık sorulan 40 soru için yerel (ücretsiz ve kotasız) sözlük kuralları
# Her kural: tetikleyici kelimeler, SQL sorgusu ve sonuç formatlayıcı fonksiyon içerir.

def format_yakit_maliyet(rows):
    tutar = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"⛽ <strong>Toplam Yakıt Maliyetimiz:</strong> {tutar:,.2f} ₺"

def format_yakit_litre(rows):
    litre = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"⛽ <strong>Toplam Tüketilen Yakıt:</strong> {litre:,.2f} Litre"

def format_en_cok_yakit_tl(rows):
    ans = "💸 <strong>En Çok Yakıt Masrafı Çıkaran Araçlar (TL):</strong><br><br>"
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - {r['sonuc']:,.2f} ₺<br>"
    return ans

def format_en_cok_yakit_lt(rows):
    ans = "🛢️ <strong>En Çok Yakıt Tüketen Araçlar (Litre):</strong><br><br>"
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - {r['sonuc']:,.2f} Litre<br>"
    return ans

def format_bakim_masrafi(rows):
    tutar = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"🔧 <strong>Toplam Bakım Maliyetimiz:</strong> {tutar:,.2f} ₺"

def format_en_cok_bakim_masrafi(rows):
    ans = "🛠️ <strong>En Çok Bakım Masrafı Çıkaran Araçlar:</strong><br><br>"
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - {r['sonuc']:,.2f} ₺<br>"
    return ans

def format_yaklasan_bakimlar(rows):
    ans = "⚠️ <strong>Bakımı Yaklaşan Araçlar:</strong><br><br>"
    if not rows: return "Şu anda bakımı yaklaşan araç bulunmuyor."
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - Hedef KM: {r['sonuc']}<br>"
    return ans

def format_ceza_tutari(rows):
    tutar = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"🚓 <strong>Toplam Trafik Cezası Tutarımız:</strong> {tutar:,.2f} ₺"

def format_hasar_tutari(rows):
    tutar = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"💥 <strong>Toplam Hasar Masrafımız:</strong> {tutar:,.2f} ₺"

def format_en_cok_ceza_sofor(rows):
    ans = "👮 <strong>En Çok Ceza Yiyen Şoförler:</strong><br><br>"
    for i, r in enumerate(rows, 1):
        sofor = r['ad'] or 'Bilinmeyen Şoför'
        ans += f"{i}. <strong>{sofor}</strong> - Toplam: {r['sonuc']:,.2f} ₺<br>"
    return ans

def format_aktif_arac_sayisi(rows):
    sayi = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"🚛 <strong>Toplam Aktif Araç Sayımız:</strong> {sayi}"

def format_kantar_toplam(rows):
    agirlik = rows[0]['sonuc'] if rows and rows[0]['sonuc'] else 0
    return f"⚖️ <strong>Kantardan Geçen Toplam Yük (Net):</strong> {agirlik:,.2f} Ton"

def format_en_cok_yuk_tasiyan(rows):
    ans = "🏋️ <strong>En Çok Yük Taşıyan Araçlar (Kantar):</strong><br><br>"
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - Toplam: {r['sonuc']:,.2f} Ton<br>"
    return ans

def format_en_cok_sevkiyat_cari(rows):
    ans = "🏢 <strong>En Çok Sevkiyat Yapılan Müşteriler/Cariler:</strong><br><br>"
    if not rows: return "Kantar tablosunda cari kayıt bulunamadı."
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['isim']}</strong> - İşlem Sayısı: {r['sonuc']}<br>"
    return ans

def format_aktif_soforler(rows):
    ans = f"👨‍✈️ <strong>Aktif Şoförlerimiz (Toplam {len(rows)}):</strong><br><br>"
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['isim']}</strong> - Tel: {r['tel'] or 'Yok'}<br>"
    return ans

def format_en_hizli_araclar(rows):
    ans = "🏎️ <strong>Hız Sınırını (80km/s) Aşan Araçlar:</strong><br><br>"
    if not rows: return "Sistemde hız sınırını aşan araç tespit edilmedi."
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - Tespit Edilen Max Hız: {r['sonuc']} km/s<br>"
    return ans

def format_odenmemis_cezalar(rows):
    ans = "📄 <strong>Ödenmemiş Cezalarımız:</strong><br><br>"
    if not rows: return "Harika! Şu an ödenmemiş bir ceza kaydı yok."
    toplam = 0
    for i, r in enumerate(rows, 1):
        ans += f"{i}. <strong>{r['plaka']}</strong> - {r['tutar']:,.2f} ₺ (Tarih: {r['tarih']})<br>"
        toplam += r['tutar']
    ans += f"<br><strong>Genel Toplam Borç:</strong> {toplam:,.2f} ₺"
    return ans

RULES = [
    # 1. Yakıt Maliyet ve Tüketim
    {
        "keywords": ["toplam yakıt maliyet", "yakıt faturası", "yakıta ne kadar", "toplam yakıt masraf"],
        "sql": "SELECT SUM(satir_tutari) as sonuc FROM yakit",
        "formatter": format_yakit_maliyet
    },
    {
        "keywords": ["kaç litre yakıt", "toplam tüketilen yakıt", "toplam yakıt hacm"],
        "sql": "SELECT SUM(yakit_miktari) as sonuc FROM yakit",
        "formatter": format_yakit_litre
    },
    {
        "keywords": ["en çok yakıt masrafı çıkaran", "yakıta en çok para", "yakıt maliyeti en yüksek"],
        "sql": "SELECT plaka, SUM(satir_tutari) as sonuc FROM yakit GROUP BY plaka ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_yakit_tl
    },
    {
        "keywords": ["en çok yakıt tüketen", "litre bazında en çok yakıt"],
        "sql": "SELECT plaka, SUM(yakit_miktari) as sonuc FROM yakit GROUP BY plaka ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_yakit_lt
    },
    
    # 2. Bakım Analizleri
    {
        "keyword_groups": [
            ["bakım", "masraf"],
            ["bakım", "maliyet"],
            ["bakım", "tutar"],
            ["bakım", "ne kadar", "tuttu"],
            ["bakım", "ne kadar", "harca"],
            ["bakıma", "ne kadar"]
        ],
        "keywords": ["toplam bakım"], # Geriye dönük uyumluluk
        "sql": "SELECT SUM(maliyet) as sonuc FROM bakim",
        "formatter": format_bakim_masrafi
    },
    {
        "keywords": ["en çok bakım masrafı çıkaran", "en fazla bakım maliyeti olan", "en masraflı araç"],
        "sql": "SELECT plaka, SUM(maliyet) as sonuc FROM bakim GROUP BY plaka ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_bakim_masrafi
    },
    {
        "keywords": ["bakım zamanı yaklaşan", "bakımı yaklaşan", "bakım kilometresi gelen"],
        "sql": "SELECT plaka, bir_sonraki_bakim_km as sonuc FROM bakim WHERE durum != 'Tamamlandı' AND bir_sonraki_bakim_km IS NOT NULL LIMIT 10",
        "formatter": format_yaklasan_bakimlar
    },

    # 3. Ceza ve Hasar
    {
        "keywords": ["toplam yediğimiz ceza", "trafik cezası tutarı", "toplam ceza maliyeti"],
        "sql": "SELECT SUM(tutar) as sonuc FROM cezalar",
        "formatter": format_ceza_tutari
    },
    {
        "keywords": ["ödenmemiş ceza", "bekleyen ceza", "ödenmeyen ceza"],
        "sql": "SELECT plaka, tutar, tarih FROM cezalar WHERE odeme_durumu != 'Ödendi'",
        "formatter": format_odenmemis_cezalar
    },
    {
        "keywords": ["en çok ceza yiyen şoför", "cezası en çok olan şoför"],
        "sql": "SELECT s.ad_soyad as ad, SUM(c.tutar) as sonuc FROM cezalar c LEFT JOIN soforler s ON c.sofor_id = s.id GROUP BY c.sofor_id ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_ceza_sofor
    },
    {
        "keywords": ["toplam hasar masraf", "hasara ne kadar", "hasar maliyeti"],
        "sql": "SELECT SUM(tutar) as sonuc FROM hasarlar",
        "formatter": format_hasar_tutari
    },

    # 4. Kantar ve Yük
    {
        "keywords": ["toplam net yük", "kantardan geçen toplam", "toplam ne kadar taşıdık"],
        "sql": "SELECT SUM(CASE WHEN birim IN ('Kg', 'kg', 'KG') THEN miktar / 1000.0 ELSE miktar END) as sonuc FROM agirlik",
        "formatter": format_kantar_toplam
    },
    {
        "keywords": ["en çok yük taşıyan", "tonajı en yüksek", "kantardan en çok geçen araç"],
        "sql": "SELECT plaka, SUM(CASE WHEN birim IN ('Kg', 'kg', 'KG') THEN miktar / 1000.0 ELSE miktar END) as sonuc FROM agirlik GROUP BY plaka ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_yuk_tasiyan
    },
    {
        "keywords": ["en çok sevkiyat yapılan cari", "en çok gittiğimiz müşteri", "en çok çalıştığımız cari"],
        "sql": "SELECT cari_adi as isim, COUNT(*) as sonuc FROM agirlik WHERE cari_adi IS NOT NULL GROUP BY cari_adi ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_cok_sevkiyat_cari
    },

    # 5. Filo ve Şoför
    {
        "keywords": ["toplam aktif araç sayıs", "kaç aracımız var"],
        "sql": "SELECT COUNT(*) as sonuc FROM araclar WHERE aktif = 1",
        "formatter": format_aktif_arac_sayisi
    },
    {
        "keywords": ["aktif şoför sayıs", "şoför listes", "kimler çalışıyor"],
        "sql": "SELECT ad_soyad as isim, telefon as tel FROM soforler WHERE aktif = 1",
        "formatter": format_aktif_soforler
    },
    
    # 6. Takip ve Performans
    {
        "keywords": ["hız sınırını aşan", "en hızlı giden", "hızlı araçlar", "80'i geçen"],
        "sql": "SELECT plaka, MAX(maksimum_hiz) as sonuc FROM arac_takip WHERE maksimum_hiz > 80 GROUP BY plaka ORDER BY sonuc DESC LIMIT 5",
        "formatter": format_en_hizli_araclar
    }
]

def check_local_queries(question):
    """
    Kullanıcının sorusunda belirtilen kilit kelimeleri tarar.
    Eğer eşleşme bulursa veritabanını sorgulayıp formatlı HTML döndürür.
    Bulamazsa None döner (Böylece sistem Auto-SQL'e veya Gemini'ye düşer).
    """
    q_lower = question.lower()
    
    # 1. Dinamik Plaka Bazlı Sorgular (Kota Limitini Aşmamak İçin Ücretsiz/Yerel)
    import re
    q_clean = re.sub(r'\s+', '', q_lower).upper()
    plate_match = re.search(r'(\d{2}[A-Z]{1,3}\d{2,4})', q_clean)
    if plate_match:
        plate = plate_match.group(1)
        
        # A. Yük/Tonaj Sorgusu
        if any(w in q_lower for w in ["yük", "ton", "taş", "çek", "kantar", "nakliye"]):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(CASE WHEN birim IN ('Kg', 'kg', 'KG') THEN miktar / 1000.0 ELSE miktar END) as toplam_yuk
                    FROM agirlik
                    WHERE plaka = ?
                """, (plate,))
                row = cursor.fetchone()
                conn.close()
                
                toplam_yuk = row['toplam_yuk'] if row and row['toplam_yuk'] else 0
                return {
                    'status': 'success',
                    'answer': f"🚚 <strong>{plate}</strong> plakalı aracın taşıdığı toplam yük miktarı:<br><br><strong>{toplam_yuk:,.2f} Ton</strong>"
                }
            except Exception as e:
                print(f"Local Plate Cargo Query Hatası: {str(e)}")

        # B. Yakıt/Mazot Sorgusu
        if any(w in q_lower for w in ["yakıt", "mazot", "benzin", "litre", "gider", "depo"]):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(yakit_miktari) as toplam_litre, SUM(satir_tutari) as toplam_tutar
                    FROM yakit
                    WHERE plaka = ?
                """, (plate,))
                row = cursor.fetchone()
                conn.close()
                
                litre = row['toplam_litre'] if row and row['toplam_litre'] else 0
                tutar = row['toplam_tutar'] if row and row['toplam_tutar'] else 0
                return {
                    'status': 'success',
                    'answer': f"⛽ <strong>{plate}</strong> plakalı aracın yakıt tüketim bilgileri:<br><br>"
                              f"• Toplam Tüketilen Yakıt: <strong>{litre:,.2f} Litre</strong><br>"
                              f"• Toplam Yakıt Gideri: <strong>{tutar:,.2f} ₺</strong>"
                }
            except Exception as e:
                print(f"Local Plate Fuel Query Hatası: {str(e)}")

        # C. Bakım/Arıza Sorgusu
        if any(w in q_lower for w in ["bakım", "tamir", "servis", "arıza"]):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as adet, SUM(maliyet) as toplam_maliyet
                    FROM bakim
                    WHERE plaka = ?
                """, (plate,))
                row = cursor.fetchone()
                conn.close()
                
                adet = row['adet'] if row and row['adet'] else 0
                maliyet = row['toplam_maliyet'] if row and row['toplam_maliyet'] else 0
                return {
                    'status': 'success',
                    'answer': f"🔧 <strong>{plate}</strong> plakalı aracın bakım bilgileri:<br><br>"
                              f"• Toplam Bakım Sayısı: <strong>{adet} adet</strong><br>"
                              f"• Toplam Bakım Gideri: <strong>{maliyet:,.2f} ₺</strong>"
                }
            except Exception as e:
                print(f"Local Plate Maintenance Query Hatası: {str(e)}")

        # D. Genel Plaka/Araç Arama Sorgusu (Araç var mı? Kayıtlı mı?)
        if any(w in q_lower for w in ["aracımız var mı", "araç var mı", "plakalı", "plaka kayıtlı", "plaka var mı", "kayıtlı mı"]):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT plaka, sahip, arac_tipi, aktif 
                    FROM araclar 
                    WHERE plaka = ? OR plaka LIKE ?
                """, (plate, f"%{plate}%"))
                results = [dict(r) for r in cursor.fetchall()]
                conn.close()
                
                if results:
                    ans = f"🔍 <strong>Veritabanında eşleşen araçlar ({len(results)} adet):</strong><br><br>"
                    for r in results:
                        durum = "Aktif" if r['aktif'] == 1 else "Pasif"
                        ans += f"• <strong>{r['plaka']}</strong> - Sahip: {r['sahip'] or 'Bilinmiyor'} - Tip: {r['arac_tipi']} ({durum})<br>"
                    return {
                        'status': 'success',
                        'answer': ans
                    }
                else:
                    return {
                        'status': 'success',
                        'answer': f"🔍 Veritabanında <strong>{plate}</strong> plakalı bir araç kaydı bulunamadı."
                    }
            except Exception as e:
                print(f"Local Plate Search Query Hatası: {str(e)}")

    # 2. Dinamik Kelime/Plaka Arama Sorgusu (Eğer tam plaka formatı eşleşmediyse ama 'plakalı' araması yapılıyorsa)
    if any(w in q_lower for w in ["aracımız var mı", "araç var mı", "plakalı", "plaka kayıtlı", "plaka var mı", "kayıtlı mı"]):
        # Soru içindeki sayısal/alfanümerik anahtar kelimeleri ayıklayalım (örn: "454")
        words = [re.sub(r'[^A-Z0-9]', '', w.upper()) for w in question.split()]
        common_words = {"BIR", "VAR", "MI", "MU", "Mİ", "MÜ", "VE", "ILE", "İLE", "İÇİN", "ICIN", "MIYIZ", "MIYIM", "ARACIMIZ", "ARAC", "ARAÇ", "PLAKALI", "PLAKA"}
        search_terms = [w for w in words if len(w) >= 2 and w not in common_words]
        
        if search_terms:
            search_term = search_terms[0]
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT plaka, sahip, arac_tipi, aktif 
                    FROM araclar 
                    WHERE plaka LIKE ?
                """, (f"%{search_term}%",))
                results = [dict(r) for r in cursor.fetchall()]
                conn.close()
                
                if results:
                    ans = f"🔍 <strong>{search_term} ile eşleşen araçlar ({len(results)} adet):</strong><br><br>"
                    for r in results:
                        durum = "Aktif" if r['aktif'] == 1 else "Pasif"
                        ans += f"• <strong>{r['plaka']}</strong> - Sahip: {r['sahip'] or 'Bilinmiyor'} - Tip: {r['arac_tipi']} ({durum})<br>"
                    return {
                        'status': 'success',
                        'answer': ans
                    }
                else:
                    return {
                        'status': 'success',
                        'answer': f"🔍 Veritabanında <strong>{search_term}</strong> ile eşleşen bir araç kaydı bulunamadı."
                    }
            except Exception as e:
                print(f"Local General Search Query Hatası: {str(e)}")

    for rule in RULES:
        matched = False
        
        # 1. Yöntem: AND Mantığı (keyword_groups)
        # Liste içindeki her bir alt listedeki kelimelerin HEPSİ cümlede geçmeli
        if "keyword_groups" in rule:
            for group in rule["keyword_groups"]:
                if all(word in q_lower for word in group):
                    matched = True
                    break
                    
        # 2. Yöntem: Birebir Cümle Eşleşmesi (keywords)
        if not matched and "keywords" in rule:
            if any(keyword in q_lower for keyword in rule["keywords"]):
                matched = True
                
        if matched:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(rule["sql"])
                rows = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                # Formatlayıcıyı çalıştır
                formatted_html = rule["formatter"](rows)
                return {
                    'status': 'success',
                    'answer': formatted_html
                }
            except Exception as e:
                print(f"Local Query Hatası: {str(e)}")
                return None
                
    return None
