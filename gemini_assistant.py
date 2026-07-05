import os
import json
import sqlite3
import pandas as pd
import io
from datetime import datetime
from database import get_db_connection, log_ai_query
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import google.generativeai as genai

from dotenv import load_dotenv
from local_queries import check_local_queries

# PythonAnywhere için .env dosyasının tam yolunu belirtiyoruz
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# API Anahtarını Çevresel Değişkenlerden (.env) Al
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("UYARI: GEMINI_API_KEY bulunamadı! Lütfen .env dosyanızı kontrol edin.")

genai.configure(api_key=GEMINI_API_KEY)

class GeminiAssistant:
    def __init__(self, model='gemini-2.5-flash'):
        self.model_name = model
        self.model = genai.GenerativeModel(self.model_name)
        self.chat_history = []
        
        # Tabloyu başlangıçta otomatik oluştur (Chicken-egg problem çözümü)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    question TEXT NOT NULL,
                    response TEXT,
                    status TEXT, -- 'success', 'error', 'fallback'
                    sql_query TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"ai_query_logs tablosu oluşturulurken hata: {e}")

    def check_gemini_status(self):
        """Gemini API servisinin çalışıp çalışmadığını kontrol et (Kota tüketmemesi için mocklandı)"""
        try:
            if self.model_name:
                return {
                    'status': 'running',
                    'models': [self.model_name],
                    'message': 'Gemini API servisi çalışıyor'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Gemini API tanımlı değil'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Gemini API\'ye bağlanılamadı: {str(e)}'
            }

    def get_context_data(self):
        """Veritabanından bağlam verisi al"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) as total FROM yakit')
            yakit_count = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(*) as total FROM araclar WHERE aktif = 1')
            arac_count = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(*) as total FROM agirlik')
            sefer_count = cursor.fetchone()['total']

            cursor.execute('SELECT plaka, arac_tipi, sahip FROM araclar WHERE aktif = 1 LIMIT 10')
            araclar = cursor.fetchall()

            conn.close()

            context = f"""
Sistem Bilgileri:
- Toplam {yakit_count} yakıt kaydı
- Toplam {arac_count} aktif araç
- Toplam {sefer_count} sefer kaydı

Aktif Araçlar (ilk 10):
"""
            for arac in araclar:
                context += f"- {arac['plaka']} ({arac['arac_tipi']}, {arac['sahip']})\n"

            return context

        except Exception as e:
            return f"Veritabanı bağlam hatası: {str(e)}"

    def query_database(self, query_type, params=None):
        """Veritabanından özel sorgu çalıştır"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if query_type == 'plaka_yakit':
                plaka = params.get('plaka')
                cursor.execute('''
                    SELECT 
                        SUM(yakit_miktari) as toplam_yakit,
                        SUM(km_fark) as toplam_km,
                        COUNT(*) as kayit_sayisi
                    FROM yakit
                    WHERE plaka = ? AND km_fark > 0 AND km_fark < 2000
                ''', (plaka,))
                row = cursor.fetchone()
                result = dict(row) if row else None
                
                # Fallback: Eğer km_fark verisi yoksa MAX-MIN dene
                if result and not result.get('toplam_km'):
                    cursor.execute('''
                        SELECT (MAX(km_bilgisi) - MIN(km_bilgisi)) as diff
                        FROM yakit WHERE plaka = ? AND km_bilgisi > 0
                    ''', (plaka,))
                    fb_row = cursor.fetchone()
                    if fb_row and fb_row['diff']:
                        result['toplam_km'] = fb_row['diff']

            elif query_type == 'en_fazla_yakit':
                cursor.execute('''
                    SELECT plaka, SUM(yakit_miktari) as toplam_yakit
                    FROM yakit
                    GROUP BY plaka
                    ORDER BY toplam_yakit DESC
                    LIMIT 5
                ''')
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]

            elif query_type == 'en_fazla_km':
                cursor.execute('''
                    SELECT plaka, SUM(km_fark) as toplam_km
                    FROM yakit
                    WHERE km_fark > 0 AND km_fark < 2000
                    GROUP BY plaka
                    ORDER BY toplam_km DESC
                    LIMIT 5
                ''')
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                
                # Eğer km_fark ile veri gelmediyse MAX - MIN ile fallback (eski veriler için)
                if not result or all(not r.get('toplam_km') for r in result):
                    cursor.execute('''
                        SELECT plaka, (MAX(km_bilgisi) - MIN(km_bilgisi)) as toplam_km
                        FROM yakit
                        WHERE km_bilgisi > 0
                        GROUP BY plaka
                        HAVING toplam_km > 0 AND toplam_km < 100000
                        ORDER BY toplam_km DESC
                        LIMIT 5
                    ''')
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]

            elif query_type == 'son_yakit_alimlari':
                limit = params.get('limit', 5) if params else 5
                cursor.execute('''
                    SELECT plaka, yakit_miktari, islem_tarihi, km_bilgisi
                    FROM yakit
                    ORDER BY islem_tarihi DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]

            elif query_type == 'aktif_araclar':
                cursor.execute('''
                    SELECT plaka, arac_tipi, sahip, aktif
                    FROM araclar
                    WHERE aktif = 1
                    ORDER BY plaka
                    LIMIT 50
                ''')
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]

            else:
                result = None

            conn.close()
            return result

        except Exception as e:
            return {'error': str(e)}

    def create_prompt(self, user_question):
        """Kullanıcı sorusuna göre prompt oluştur"""
        context = self.get_context_data()

        system_prompt = f"""Sen Kargo/Beton şirketinin baş asistanısın. 
Cevaplarında her zaman çok ciddi ve resmi ol. SADECE TÜRKÇE konuş!

Şoförlerin hız sınırı 80 km/s'dir. Eğer yakıt, performans veya takip sorulursa, hız sınırını aşıp aşmadıklarını da kontrol edip uyar.
Ayrıca verileri yaptığı işe göre değerlendirerek yöneticilere maliyet analizi sun.

ÖNEMLİ: Bu veritabanı sütunları, satırları ve matematiksel hesaplamalar işletmenin kârlılık kararları için hayati önem taşır. Hesaplamalarda hataya kesinlikle yer yoktur. Sonuçları vermeden önce adımları ve değerleri (miktar, net_agirlik vb.) dikkatle doğrula.

Sana verilen sistem bilgilerini kullanarak kullanıcının sorularına kısa, net, profesyonel ve analitik cevaplar ver.

Sistem Bilgileri:
{context}

Kullanıcı Sorusu: {user_question}

TÜRKÇE ve RESMİ cevap ver:"""

        return system_prompt

    def safe_generate_content(self, prompt, retries=3, delay=2):
        """Gemini API çağrılarını kota aşımına (429) karşı otomatik yeniden deneme mantığıyla çalıştırır"""
        import time
        for i in range(retries):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "quota" in err_msg or "rate limit" in err_msg:
                    if i < retries - 1:
                        wait_time = delay * (i + 1)
                        print(f"Gemini API Kota Aşımı (429) algılandı. {wait_time} saniye bekleniyor... (Deneme {i+1}/{retries})")
                        time.sleep(wait_time)
                        continue
                raise e

    def ask(self, question, stream=False):
        """Gemini'ye soru sor"""
        try:
            prompt = self.create_prompt(question)
            
            response = self.safe_generate_content(prompt)

            if response.text:
                response_text = response.text
                
                self.chat_history.append({
                    'question': question,
                    'answer': response_text,
                    'timestamp': datetime.now().isoformat()
                })

                return {
                    'status': 'success',
                    'answer': response_text,
                    'model': self.model_name
                }
            else:
                return {
                    'status': 'error',
                    'message': 'API yanıt döndürmedi.'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Hata: {str(e)}'
            }

    def check_ml_queries(self, question):
        """Kullanıcı sorusuna göre Python ML modellerini (ai_model.py) tetikler ve Gemini ile yorumlatır"""
        question_lower = question.lower()
        
        # 1. ANOMALİ TESPİTİ
        if any(w in question_lower for w in ['anomali', 'şüpheli', 'anormal', 'suistimal', 'usulsüz']):
            try:
                from ai_model import AnomalTespitModeli
                model = AnomalTespitModeli()
                res = model.anomali_tespit()
                if res['status'] == 'success':
                    anomaliler = res['anomaliler']
                    prompt = f'''Aşağıda şirketimizin yakıt veritabanı işlemlerine ait Isolation Forest (Yapay Zeka) anomali tespit modelinin sonuçları yer almaktadır:
                    {anomaliler[:10]}
                    
                    Lütfen bu veriyi kullanarak şüpheli işlemleri (aşırı yakıt alanlar, kilometresi girilmeyenler vb.) analiz et.
                    Yöneticiler için resmi, dostça, HTML destekli (örn: <strong>kalın</strong>, <br> satır atlama) ve aksiyon öneren Türkçe bir rapor yaz. Asla koddan veya model yapısından bahsetme.'''
                    
                    response = self.safe_generate_content(prompt)
                    return {
                        'status': 'success',
                        'answer': "🤖 🧠 <em>(AI Anomali Analiz Raporu)</em><br><br>" + response.text
                    }
            except Exception as e:
                print(f"ML Anomali Hatası: {e}")
                
        # 2. VERİMLİLİK VE PERFORMANS KARŞILAŞTIRMASI
        if any(w in question_lower for w in ['verimlilik', 'verimsiz', 'performans', 'karşılaştır']):
            try:
                from ai_model import PerformansAnalizi
                model = PerformansAnalizi()
                res = model.plaka_performans_karsilastirma()
                if res['status'] == 'success':
                    en_verimli = res['en_verimli']
                    en_verimsiz = res['en_verimsiz']
                    prompt = f'''Aşağıda araçlarımızın yakıt/km oranlarına göre performans analizi sonuçları yer almaktadır:
                    En Verimli Araçlar: {en_verimli}
                    En Verimsiz Araçlar: {en_verimsiz}
                    
                    Lütfen bu verileri kullanarak en iyi ve en kötü performans gösteren araçları kıyasla.
                    Hangi araçların bakıma girmesi gerektiği veya şoför performansları hakkında yorumlar ekle.
                    Yöneticiler için resmi, HTML destekli (örn: <strong>kalın</strong>, <br> satır atlama) Türkçe bir rapor yaz.'''
                    
                    response = self.safe_generate_content(prompt)
                    return {
                        'status': 'success',
                        'answer': "🤖 📊 <em>(AI Performans Karşılaştırma Raporu)</em><br><br>" + response.text
                    }
            except Exception as e:
                print(f"ML Performans Hatası: {e}")
                
        # 3. YAKIT TÜKETİM TAHMİNİ
        if any(w in question_lower for w in ['tahmin', 'gelecek ay', 'gelecekte', 'önümüzdeki ay']):
            try:
                # Plakayı bulmaya çalışalım (Örn: 34ABC123)
                import re
                plaka_match = re.search(r'\b\d{2}[a-zA-Z]{1,3}\d{2,4}\b', question.upper().replace(" ", ""))
                if plaka_match:
                    plaka = plaka_match.group(0)
                    from ai_model import YakitTahminModeli
                    model = YakitTahminModeli()
                    res = model.gelecek_ay_tahmini(plaka)
                    if res['status'] == 'success':
                        tahmin_toplam = res['toplam_tahmin']
                        tahminler = res['tahminler']
                        prompt = f'''Aşağıda {plaka} plakalı aracımızın gelecek 30 günlük yakıt tüketimi tahmin (Random Forest Regressor) sonuçları yer almaktadır:
                        Gelecek 30 Günlük Toplam Yakıt Tahmini: {tahmin_toplam} Litre.
                        Günlük Tahminlerden Bazıları: {tahminler[:5]}
                        
                        Lütfen bu tahmin sonuçlarını kullanarak aracın gelecek dönem yakıt maliyeti ve bütçesi hakkında yorum yap.
                        Yöneticiler için resmi, HTML destekli Türkçe bir rapor yaz.'''
                        
                        response = self.safe_generate_content(prompt)
                        return {
                            'status': 'success',
                            'answer': f"🤖 🔮 <em>(AI Tüketim Tahmin Raporu: {plaka})</em><br><br>" + response.text
                        }
            except Exception as e:
                print(f"ML Tahmin Hatası: {e}")
                
        return None

    def ask_with_db_query(self, question, last_plate=None):
        """Sorguyu çalıştıran ve ardından log tablosuna kaydeden sarmal metot"""
        res = self._ask_with_db_query_impl(question, last_plate)
        
        # SQL loglama altyapısı
        try:
            from flask import session
            username = session.get('username', 'system')
        except:
            username = 'system'
            
        try:
            status = res.get('status', 'success')
            answer = res.get('answer', '')
            sql_query = res.get('sql_query', None)
            error_message = res.get('error_message', None)
            
            # Eğer genel sohbete düştüyse status 'fallback' yapılır
            if status == 'success' and sql_query is None and "🤖" not in answer and "🏆" not in answer and "📋" not in answer and "🏎️" not in answer and "🚗" not in answer:
                status = 'fallback'
                
            log_ai_query(username, question, answer, status, sql_query, error_message)
        except Exception as e:
            print(f"Loglama hatası: {e}")
            
        return res

    def _ask_with_db_query_impl(self, question, last_plate=None):
        """Veritabanı sorgusu ile desteklenmiş soru - İç Mantık"""
        import re
        def format_plaka(match):
            return (match.group(1) + match.group(2) + match.group(3)).upper()
        # Plakaları standart formata çevir (Örn: 46 ahr 076 -> 46AHR076)
        question = re.sub(r'\b([0-9]{2})\s*([a-zA-ZçÇğĞıİöÖşŞüÜ]{1,3})\s*([0-9]{2,4})\b', format_plaka, question)
        question_lower = question.lower()
        
        db_result = None
        export_type = None

        # Excel veya PDF talebi kontrolü
        if 'excel' in question_lower and ('ver' in question_lower or 'yap' in question_lower or 'oluştur' in question_lower or 'indir' in question_lower or 'çıkart' in question_lower or 'formatında' in question_lower):
            export_type = 'excel'
        elif 'pdf' in question_lower and ('ver' in question_lower or 'yap' in question_lower or 'oluştur' in question_lower or 'indir' in question_lower or 'çıkart' in question_lower or 'formatında' in question_lower):
            export_type = 'pdf'

        # 1. YENİ SÖZLÜK SİSTEMİ (Yerel Ücretsiz Kısayollar)
        local_result = check_local_queries(question, last_plate)
        if local_result and not export_type:
            return local_result

        # 2. PYTHON ML MODELLERİ (AI Tahmin, Anomali, Verimlilik)
        ml_result = self.check_ml_queries(question)
        if ml_result:
            return ml_result

        # Sorgu türünü belirle ve DIREKT YANITLA (Eski kurallar)
        if 'en fazla yakıt' in question_lower or 'en çok yakıt' in question_lower:
            db_result = self.query_database('en_fazla_yakit')
            if db_result and not export_type:
                # Direkt yanıt ver, AI'ya sorma
                answer = "🏆 <strong>En Fazla Yakıt Tüketen Araçlar:</strong><br><br>"
                for i, arac in enumerate(db_result, 1):
                    answer += f"{i}. <strong>{arac['plaka']}</strong> - {arac['toplam_yakit']:.2f} Litre<br>"
                return {'status': 'success', 'answer': answer}

        elif 'son yakıt' in question_lower or 'son alım' in question_lower:
            db_result = self.query_database('son_yakit_alimlari', {'limit': 10})
            if db_result and not export_type:
                answer = "📋 <strong>Son Yakıt Alımları:</strong><br><br>"
                for i, kayit in enumerate(db_result, 1):
                    answer += f"{i}. <strong>{kayit['plaka']}</strong> - {kayit['yakit_miktari']:.2f}L - {kayit['islem_tarihi']} - {kayit['km_bilgisi']} km<br>"
                return {'status': 'success', 'answer': answer}

        elif 'aktif araç' in question_lower or 'araç listesi' in question_lower:
            db_result = self.query_database('aktif_araclar')
            if db_result and not export_type:
                answer = f"🚛 <strong>Aktif Araçlar (Toplam: {len(db_result)}):</strong><br><br>"
                for i, arac in enumerate(db_result[:20], 1):
                    answer += f"{i}. <strong>{arac['plaka']}</strong> - {arac['arac_tipi']} ({arac['sahip']})<br>"
                if len(db_result) > 20:
                    answer += f"<br><em>... ve {len(db_result) - 20} araç daha</em>"
                return {'status': 'success', 'answer': answer}

        elif 'kilometre' in question_lower or 'km' in question_lower or 'en çok yol' in question_lower:
            db_result = self.query_database('en_fazla_km')
            if db_result and not export_type:
                answer = "🏎️ <strong>En Çok Kilometre Yapan Araçlar:</strong><br><br>"
                for i, arac in enumerate(db_result, 1):
                    km = arac.get('toplam_km') or 0
                    answer += f"{i}. <strong>{arac['plaka']}</strong> - {km:,.0f} km<br>"
                return {'status': 'success', 'answer': answer}

        elif any(keyword in question_lower for keyword in ['plaka', 'araç']):
            if 'ne zaman' not in question_lower and 'son' not in question_lower and 'nerede' not in question_lower:
                words = question.split()
                for word in words:
                    if len(word) > 5 and word.isupper() and any(c.isalpha() for c in word):
                        db_result = self.query_database('plaka_yakit', {'plaka': word})
                        if db_result and db_result.get('toplam_yakit'):
                            answer = f"🚗 <strong>{word} Yakıt Bilgileri:</strong><br><br>"
                            answer += f"• Toplam Yakıt: <strong>{db_result.get('toplam_yakit', 0):.2f} Litre</strong><br>"
                            answer += f"• Toplam KM: <strong>{db_result.get('toplam_km', 0):,} km</strong><br>"
                            answer += f"• Kayıt Sayısı: <strong>{db_result.get('kayit_sayisi', 0)}</strong>"
                            return {'status': 'success', 'answer': answer}
                        break

        # Eğer export isteniyor ama spesifik sorgu yok ise, aktif araçları ver
        if export_type and not db_result:
            if 'bunu' in question_lower or 'sistem' in question_lower or 'durum' in question_lower:
                db_result = self.query_database('aktif_araclar')

        # Excel veya PDF oluştur
        if export_type and db_result:
            if export_type == 'excel':
                file_data = self.create_excel(db_result, question)
                return {
                    'status': 'success',
                    'answer': 'Excel dosyası hazırlandı. İndirmek için aşağıdaki linke tıklayın.',
                    'export_type': 'excel',
                    'file_data': file_data,
                    'filename': f'rapor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                }
            elif export_type == 'pdf':
                file_data = self.create_pdf(db_result, question)
                return {
                    'status': 'success',
                    'answer': 'PDF dosyası hazırlandı. İndirmek için aşağıdaki linke tıklayın.',
                    'export_type': 'pdf',
                    'file_data': file_data,
                    'filename': f'rapor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                }

        context = self.get_context_data()
        
        # Eğer özel bir sorgu değilse Auto-SQL ajanına (Kendi Kendine Sorgu Yazan) gönder
        return self.auto_sql_agent(question)

    def get_database_schema(self):
        return """
        Veritabanı Şeması (SQLite):
        - yakit (id, plaka, islem_tarihi, saat, yakit_miktari, birim_fiyat, satir_tutari, stok_adi, km_bilgisi, km_fark, litre_km, toplam_yuk, ton_litre, fis_fotograf_yolu, sofor_id)
        - araclar (id, plaka, sahip, arac_tipi, aktif, notlar)
        - bakim (id, plaka, bakim_tipi, yapilan_islem, tarih, km, maliyet, bir_sonraki_bakim_km, bir_sonraki_bakim_tarih, servis_adi, durum)
        - soforler (id, ad_soyad, telefon, tc_no, aktif)
        - cezalar (id, plaka, sofor_id, tarih, tutar, aciklama, odeme_durumu)
        - hasarlar (id, plaka, sofor_id, tarih, tutar, aciklama, sigorta_karsiladi_mi)
        - seferler (id, sofor_id, plaka, baslangic_zaman, bitis_zaman, baslangic_km, bitis_km, durum)
        - agirlik (id, tarih, miktar, birim, net_agirlik, plaka, adres, islem_noktasi, cari_adi, ana_malzeme)
        - ai_query_logs (id, username, question, response, status, sql_query, error_message, created_at)
          * NOT 1: agirlik tablosunda 'miktar' sütunu taşınan yük/malzeme miktarını gösterir (birim 'Kg' ise miktar/1000.0 tonajı verir).
          * NOT 2: agirlik tablosunda 'net_agirlik' sütunu aslında yükü değil aracın boş ağırlığını (dara) gösterir. Yük/tonaj hesaplarken net_agirlik'i SUM(net_agirlik) olarak KULLANMA, miktar'ı kullan.
          * NOT 3: agirlik tablosunda 'ana_malzeme' sütunu malzeme türünü gösterir (Örn: 'BETON', 'KUM', 'PARKE', 'BORDRO', 'PALET').
          * NOT 4: ai_query_logs tablosunda asistana sorulan sorular (question), asistanın verdiği yanıtlar (response), durumu (status: 'success' [başarılı], 'fallback' [sohbete düşen] veya 'error' [hata alan]) ve log zamanı (created_at) tutulur. Asistan sorgu geçmişi veya loglar sorulduğunda bu tabloyu kullan.
        """

    def auto_sql_agent(self, question):
        """Kullanıcının sorusundan dinamik olarak SQL üretip veritabanında çalıştırır"""
        try:
            import re
            schema = self.get_database_schema()
            
            # Aşama 1: SQL Üretimi
            sql_prompt = f'''Sen uzman bir veritabanı mühendisisin.
            Aşağıdaki SQLite veritabanı şemasına dayanarak, kullanıcının sorusunu cevaplayacak SADECE BİR adet 'SELECT' sorgusu yaz.
            ÖNEMLİ KURAL 1: Plaka bilgileri veritabanında HER ZAMAN BÜYÜK HARFLE ve BİTİŞİK tutulur (Örn: 34ABC123). Plaka ararken tam eşleşme (plaka = '46AHR076') kullan.
            ÖNEMLİ KURAL 2: Soru "mazot", "benzin", "yakıt" içeriyorsa 'stok_adi' sütununa göre FİLTRELEME YAPMA. Yakıt tablosundaki tüm kayıtlar zaten yakıt alımıdır.
            ÖNEMLİ KURAL 3: agirlik tablosunda taşınan yük miktarı 'miktar' sütunundadır (eğer birim 'Kg' ise miktar/1000.0 ton değerini verir). 'net_agirlik' sütunu ise aracın boş ağırlığını (dara) tutar. Bu yüzden taşınan yük/tonaj sorulduğunda veya hesaplandığında net_agirlik yerine HER ZAMAN miktar sütununu kullan.
            ÖNEMLİ KURAL 4: Bu veritabanı sütunları ve satırları işletmenin kârlılık ve maliyet hesapları için hayati derecede önemlidir. Matematiksel hesaplamalarda ve sütun eşleştirmelerinde HATA YAPMAYA KESİNLİKLE YER YOKTUR. Dara (net_agirlik) ve net yük (miktar) arasındaki ayrımı kusursuz uygula.
            ÖNEMLİ KURAL 5: Soruda geçen "malzeme", "yük" veya "ürün" genel ifadeleri için 'ana_malzeme' sütununa filtre uygulama (Örn: ana_malzeme = 'malzeme' yapma). Çünkü bu genel ifadeler tablodaki tüm kayıtları kapsar. Sadece kullanıcı "beton", "kum", "parke", "bordro", "palet" gibi veritabanında var olan spesifik bir malzemeyi sorarsa ana_malzeme sütununa filtre koy.
            
            ÖNEMLİ İŞ KURALLARI:
            - KURAL 6 (Özmal Araçlar): "Bizim araçlar" veya "özmal araçlar" sorgulandığında, `araclar` tablosundaki `sahip = 'BİZİM'` filtresini ekle.
            - KURAL 7 (Taşeron/Dış/Kiralık): "Taşeron", "dış araç", "kiralık" veya "yabancı" araçlar sorulduğunda, `araclar` tablosundaki `sahip = 'TAŞERON'` (veya `sahip != 'BİZİM'`) filtresini ekle.
            - KURAL 8 (Araç Tipleri): "Kamyon" veya "kargo" denirse `arac_tipi = 'KARGO ARACI'`, "kepçe", "dozer", "silindir" veya "iş makinesi" denirse `arac_tipi = 'İŞ MAKİNESİ'`, "binek" veya "otomobil" denirse `arac_tipi = 'BİNEK ARAÇ'` filtrelemesini yap.
            - KURAL 9 (Hız Sınırı ve Hız Aşımı): Hız sınırı aşımı yapan veya aşırı hızlı giden araçlar sorulursa, `arac_takip` tablosunda `maksimum_hiz > 80` kriterini kullan (Şirket hız limiti 80 km/s'dir).
            - KURAL 10 (Yakıt Verimliliği): En verimli, en az yakan veya en yüksek verimli araçlar sorulursa, bu araçlar HER ZAMAN şirket bünyesindeki özmal araçlar olmalıdır. Dolayısıyla, `yakit` tablosunu `araclar` tablosuyla `plaka` sütunu üzerinden INNER JOIN yapıp `araclar.sahip = 'BİZİM'` filtresi uygulayarak (taşeron araçlarını tamamen hariç tutarak) ve `km_fark > 0` şartı koyarak, 100 km'deki yakıt tüketimini şu şekilde hesapla: `(SUM(yakit_miktari) * 100.0) / SUM(km_fark)` oranı en düşük olan aracı getir.
            - KURAL 11 (Ödenmemiş Trafik Cezaları): "Ödenmemiş cezalar", "ceza borcu" veya "bekleyen cezalar" sorulduğunda, `cezalar` tablosunda `odeme_durumu != 'Ödendi'` (veya `odeme_durumu = 'Ödenmedi'`) filtresini kullan.
            - KURAL 12 (Şirketin Ödediği Hasarlar): "Cebimizden çıkan", "şirketin ödediği" veya "sigortanın karşılamadığı" hasarlar sorulursa, `hasarlar` tablosunda `sigorta_karsiladi_mi = 0` (veya `False`) filtresini ekle.
            - KURAL 13 (Bekleyen Araç Bakımları): "Bekleyen bakımlar", "yapılacak bakımlar" veya "zamanı gelen bakımlar" sorulduğunda, `bakim` tablosunda `durum != 'Tamamlandı'` filtresini uygula.
            
            Cevabın SADECE SQL kodu olmalı, hiçbir açıklama veya markdown backtick (```sql) GEREKMEZ, sadece saf SQL kodunu ver.
            Kullanıcının sorusu: {question}
            Şema: {schema}'''
            
            response = self.safe_generate_content(sql_prompt)
            sql_code = response.text.strip()
            
            # Markdown kalıntılarını temizle (```sql ... ```)
            match = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql_code, re.DOTALL | re.IGNORECASE)
            if match:
                sql_code = match.group(1).strip()
            
            # Sadece SELECT sorgularına izin ver, güvenlik için UPDATE/DELETE engeli
            if not sql_code.upper().startswith("SELECT"):
                fallback_res = self.ask(question)
                fallback_res['status'] = 'fallback'
                return fallback_res

            # Aşama 2: Veritabanında Çalıştırma
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql_code)
            rows = cursor.fetchall()
            db_result = [dict(row) for row in rows]
            conn.close()

            # Aşama 3: İnsancıl Cevap Üretimi
            answer_prompt = f'''Sen Kargo/Beton şirketinin profesyonel yapay zeka asistanısın. Sadece Türkçe yanıt ver.
            Kullanıcının sorusu: {question}
            Kullanıcının sorusu için çalıştırılan sorgu sonucu elde edilen veri: {db_result}
            
            Lütfen bu veriyi kullanarak kullanıcıya resmi, açık, HTML destekli (örn: <strong>kalın</strong>, <br> satır atlama) güzel bir Türkçe cevap hazırla. Asla SQL kodundan veya veritabanı yapısından bahsetme. Doğrudan sonuçları sun.
            Eğer veri boş liste ([]) ise "İstediğiniz kriterlere uygun veri bulunamadı." gibi kibar bir mesaj ver.'''
            
            final_response = self.safe_generate_content(answer_prompt)
            
            return {
                'status': 'success',
                'answer': "🤖 <em>(Auto-SQL Analizi)</em><br><br>" + final_response.text,
                'sql_query': sql_code
            }
        except Exception as e:
            # SQL hataları veya yetki sorunları olursa standart sohbet moduna geri dön
            print(f"Auto-SQL Hatası: {str(e)}")
            fallback_res = self.ask(question)
            # Loglama ve hata takibi için hata mesajını ekle
            fallback_res['error_message'] = str(e)
            return fallback_res

    def get_chat_history(self):
        """Sohbet geçmişini getir"""
        return self.chat_history

    def clear_history(self):
        """Sohbet geçmişini temizle"""
        self.chat_history = []
        return {'status': 'success', 'message': 'Geçmiş temizlendi'}

    def create_excel(self, data, question):
        """Veritabanı sonuçlarından Excel dosyası oluştur"""
        output = io.BytesIO()
        
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()

        # Sütun isimlerini Türkçeleştir
        column_mapping = {
            'plaka': 'Plaka',
            'arac_tipi': 'Araç Tipi',
            'sahip': 'Sahip',
            'aktif': 'Durum',
            'toplam_yakit': 'Toplam Yakıt (L)',
            'toplam_km': 'Toplam KM',
            'kayit_sayisi': 'Kayıt Sayısı',
            'yakit_miktari': 'Yakıt Miktarı (L)',
            'islem_tarihi': 'İşlem Tarihi',
            'km_bilgisi': 'KM Bilgisi'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Rapor', index=False)
            
        output.seek(0)
        return output.getvalue()

    def create_pdf(self, data, question):
        """Veritabanı sonuçlarından PDF dosyası oluştur"""
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Başlık
        title = Paragraph(f"<b>Rapor</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Tarih
        date_text = Paragraph(f"Oluşturma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal'])
        elements.append(date_text)
        elements.append(Spacer(1, 12))

        # Veriyi tabloya dönüştür
        if isinstance(data, list) and len(data) > 0:
            # Sütun başlıkları
            headers = list(data[0].keys())
            table_data = [headers]
            
            # Satırlar
            for row in data:
                table_data.append([str(row[key]) for key in headers])
                
            # Tablo oluştur
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

        doc.build(elements)
        output.seek(0)
        return output.getvalue()

# Dışa aktarılacak yardımcı fonksiyonlar
assistant = GeminiAssistant()

def check_gemini_status():
    return assistant.check_gemini_status()

def ask_gemini(question, model=None, conversation_history=None):
    if model:
        assistant.model_name = model
        assistant.model = genai.GenerativeModel(model)
        
    return assistant.ask_with_db_query(question)

def get_quick_insights():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(yakit_miktari) as toplam 
            FROM yakit 
            WHERE islem_tarihi >= date('now', '-30 days')
        ''')
        row = cursor.fetchone()
        son_30_gun = row['toplam'] if row['toplam'] else 0
        
        cursor.execute('''
            SELECT SUM(yakit_miktari) as toplam 
            FROM yakit 
            WHERE islem_tarihi >= date('now', '-7 days')
        ''')
        row = cursor.fetchone()
        son_7_gun = row['toplam'] if row['toplam'] else 0
        
        conn.close()
        
        return [
            f"Son 30 günde toplam {son_30_gun:.1f}L yakıt tüketildi.",
            f"Son 7 günde {son_7_gun:.1f}L yakıt alımı yapıldı.",
            "En yüksek tüketim yapan aracı bulmak için 'en fazla yakıt' yazabilirsiniz."
        ]
    except Exception as e:
        return ["Sistem durumu şu an alınamıyor."]

def ask_support_gemini(question):
    """
    Teknik Destek Asistanı - Sistem kullanımı, hata giderme ve kılavuzluk sağlar.
    """
    try:
        support_prompt = f"""Sen Anti-Gravity Telematik ve Filo Yönetim Sisteminin Teknik Destek Asistanısın.
Kullanıcılara sistemin kullanımı, karşılaştıkları hataların çözümleri ve sayfaların işlevleri hakkında yardım ediyorsun.
Cevaplarında her zaman çok profesyonel, kibar ve çözüm odaklı ol. SADECE TÜRKÇE konuş!

Sistem Kullanım Kılavuzu:
1. Dashboard (Ana Sayfa): Yakıt tahminleri, sistem genel istatistikleri ve grafikler yer alır.
2. Otomatik Veri Çekme (Sync): Excel/CSV formatındaki yakıt, kantar veya takip dosyalarını sisteme yüklemek için kullanılır. Sürükle-bırak veya dosya seçerek "Yükle" (Upload) butonu kullanılır.
3. Veri Yönetimi (Data Management): Yakıt fişleri, kantar verileri ve araç konum takip kayıtlarının listelendiği alandır.
4. Muhasebe Analizi: Yakıt giderleri, taşeron maliyetleri ve kârlılık analizlerini içerir.
5. Filo Yönetimi: Araç ekleme, güncelleme, silme ve sahiplik durumunu (BİZİM/TAŞERON) yönetme ekranıdır. "Make it all OUR" butonu ile tek tıkla tüm araçlar şirket aracı yapılabilir.
6. Bakım & Onarım: Araç bakım kayıtları, km ve maliyet girişleri yapılır.
7. AI Analiz: Yakıt anomalileri ve yapay zeka analiz raporlarını sunar.
8. Şoför Yönetimi: Şoförlerin telefon, lisans ve aktiflik bilgilerini yönetir.
9. Lastik Yönetimi: Lastik ömürleri, takılan pozisyonlar ve km takibini yönetir.
10. Hasar & Ceza: Araç hasarları, trafik cezaları ve sorumlu şoför takibini yönetir.
11. Kullanıcı Yönetimi: Yönetici (admin) hesabı ile yeni sistem kullanıcıları tanımlanır.

Sık Karşılaşılan Sorular ve Çözümler:
- "Yakıt verisini veya Excel'i nasıl yüklerim?": Otomatik Veri Çekme (Sync) sayfasına gidin. Yakıt Excel dosyasını seçip yükleyin. Sistem, 'mazot', 'benzin', 'litre', 'miktar' gibi farklı yazılmış sütunları akıllı algoritmasıyla otomatik eşleştirecektir.
- "Veri yüklerken yeni bir sütun ekledik, ne yapmalıyım?": Hiçbir şey yapmanıza gerek yok. Sistemimiz, veritabanında olmayan yeni Excel sütunlarını otomatik algılayıp veritabanını dinamik olarak genişletir (Auto-Alter Table).
- "Hata aldığımda ne yapmalıyım?": Hatanın hangi sayfada olduğunu ve hata kodunu (örn. 500, 404) destek paneline yazarsanız size adım adım çözüm önerisinde bulunabilirim.

Kullanıcı Sorusu: {question}

Lütfen bu bilgilere göre kullanıcıya HTML destekli (örn: <strong>kalın</strong>, <br> satır atlama) açıklayıcı ve profesyonel bir cevap hazırla:"""

        # Gemini modelini kullanarak yanıt üret
        response = assistant.safe_generate_content(support_prompt)
        if response.text:
            return {
                'status': 'success',
                'answer': "🛠️ <strong>Teknik Destek AI Asistanı:</strong><br><br>" + response.text
            }
        else:
            return {
                'status': 'error',
                'message': 'API yanıt döndürmedi.'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }
