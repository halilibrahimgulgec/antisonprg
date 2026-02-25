import requests
import json
import sqlite3
import pandas as pd
import io
from datetime import datetime
from database import get_db_connection
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class OllamaAssistant:
    def __init__(self, model='llama3.2', base_url='http://localhost:11434'):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.chat_history = []

    def check_ollama_status(self):
        """Ollama servisinin çalışıp çalışmadığını kontrol et"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    'status': 'running',
                    'models': [m['name'] for m in models],
                    'message': 'Ollama servisi çalışıyor'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ollama servisine bağlanılamadı: {str(e)}'
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

        system_prompt = f"""Sen kargo yönetim sistemi asistanısın. SADECE TÜRKÇE konuş!

Sistem Bilgileri:
{context}

Kullanıcı Sorusu: {user_question}

TÜRKÇE cevap ver (kısa ve net):"""

        return system_prompt

    def ask(self, question, stream=False):
        """Ollama'ya soru sor"""
        try:
            prompt = self.create_prompt(question)

            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': stream
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                if stream:
                    return response
                else:
                    response_text = ''
                    for line in response.text.strip().split('\n'):
                        if line:
                            json_response = json.loads(line)
                            response_text += json_response.get('response', '')
                            if json_response.get('done', False):
                                break

                    self.chat_history.append({
                        'question': question,
                        'answer': response_text,
                        'timestamp': datetime.now().isoformat()
                    })

                    return {
                        'status': 'success',
                        'answer': response_text,
                        'model': self.model
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'API hatası: {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'Zaman aşımı. Ollama yanıt vermedi (60 saniye).'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Hata: {str(e)}'
            }

    def ask_with_db_query(self, question):
        """Veritabanı sorgusu ile desteklenmiş soru"""
        question_lower = question.lower()

        db_result = None
        export_type = None

        # Excel veya PDF talebi kontrolü
        if 'excel' in question_lower and ('ver' in question_lower or 'yap' in question_lower or 'oluştur' in question_lower or 'indir' in question_lower or 'çıkart' in question_lower or 'formatında' in question_lower):
            export_type = 'excel'
        elif 'pdf' in question_lower and ('ver' in question_lower or 'yap' in question_lower or 'oluştur' in question_lower or 'indir' in question_lower or 'çıkart' in question_lower or 'formatında' in question_lower):
            export_type = 'pdf'

        # Sorgu türünü belirle ve DIREKT YANITLA
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

        elif any(keyword in question_lower for keyword in ['plaka', 'araç']):
            words = question.split()
            for word in words:
                if len(word) > 5 and word.isupper():
                    db_result = self.query_database('plaka_yakit', {'plaka': word})
                    if db_result:
                        answer = f"🚗 <strong>{word} Yakıt Bilgileri:</strong><br><br>"
                        answer += f"• Toplam Yakıt: <strong>{db_result['toplam_yakit']:.2f} Litre</strong><br>"
                        answer += f"• Toplam KM: <strong>{db_result['toplam_km']:,} km</strong><br>"
                        answer += f"• Kayıt Sayısı: <strong>{db_result['kayit_sayisi']}</strong>"
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

        if db_result:
            context += f"\n\nVeritabanı Sorgu Sonucu:\n{json.dumps(db_result, indent=2, ensure_ascii=False)}"

        return self.ask(question)

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

def test_ollama():
    """Ollama test fonksiyonu"""
    assistant = OllamaAssistant()

    status = assistant.check_ollama_status()
    print("Ollama Durumu:", status)

    if status['status'] == 'running':
        print("\nTest sorusu soruluyor...")
        result = assistant.ask("Merhaba, sen kimsin?")
        print("\nYanıt:", result)

    return status

if __name__ == '__main__':
    test_ollama()
