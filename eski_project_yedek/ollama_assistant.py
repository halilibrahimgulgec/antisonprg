import requests
import json
from database import get_ai_context, get_db_stats

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"


def check_ollama_status():
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            return {'available': True, 'models': [m['name'] for m in models]}
        return {'available': False, 'models': []}
    except:
        return {'available': False, 'models': []}


def build_system_prompt(context):
    stats = get_db_stats()
    yakit_ozet = context.get('yakit_ozet', [])
    araclar = context.get('araclar', [])
    agirlik = context.get('agirlik_ozet', [])

    arac_listesi = '\n'.join([
        f"  - {a['plaka']}: {a.get('arac_tipi','?')} / {a.get('sahip','?')} / {'Aktif' if a.get('aktif') else 'Pasif'}"
        for a in araclar[:20]
    ])

    yakit_listesi = '\n'.join([
        f"  - {y['plaka']} ({y['ay']}): {y['toplam_yakit']:.1f}L, {y['toplam_maliyet']:.2f}₺, {y['islem_sayisi']} işlem"
        for y in yakit_ozet[:20]
    ])

    agirlik_listesi = '\n'.join([
        f"  - {a['plaka']}: {a['toplam_ton']:.1f} ton, {a['sefer']} sefer"
        for a in agirlik[:10]
    ])

    return f"""Sen bir kargo şirketi veri analisti asistanısın. Aşağıdaki veritabanı verilerini kullanarak Türkçe ve net cevaplar ver.

VERİTABANI ÖZETİ:
- Toplam yakıt kaydı: {stats.get('yakit_kayit', 0)}
- Toplam yakıt tüketimi: {stats.get('toplam_yakit', 0):.1f} litre
- Toplam yakıt maliyeti: {stats.get('toplam_maliyet', 0):.2f} ₺
- Aktif araç sayısı: {stats.get('aktif_arac', 0)}
- Toplam ağırlık kaydı: {stats.get('agirlik_kayit', 0)}
- Toplam taşınan yük: {stats.get('toplam_agirlik', 0):.1f} ton

ARAÇ LİSTESİ:
{arac_listesi if arac_listesi else '  Kayıt yok'}

AYLIK YAKIT TÜKETİMLERİ (Son dönem):
{yakit_listesi if yakit_listesi else '  Kayıt yok'}

AĞIRLIK/TONAJ VERİLERİ:
{agirlik_listesi if agirlik_listesi else '  Kayıt yok'}

Kurallar:
1. Sadece yukarıdaki verilerle cevap ver.
2. Türkçe yaz, net ve kısa ol.
3. Sayısal veriler için gerçek değerleri kullan.
4. Veri yoksa 'Bu konuda veri bulunamadı' de.
5. Önerilerde bulun ama abartma.
"""


def ask_ollama(question, model=None, conversation_history=None):
    if model is None:
        model = DEFAULT_MODEL

    status = check_ollama_status()
    if not status['available']:
        return {
            'success': False,
            'answer': 'Ollama servisi çalışmıyor. Lütfen `ollama serve` komutunu çalıştırın.',
            'model': model
        }

    if model not in status['models'] and status['models']:
        model = status['models'][0]

    context = get_ai_context()
    system_prompt = build_system_prompt(context)

    messages = [{'role': 'system', 'content': system_prompt}]

    if conversation_history:
        messages.extend(conversation_history[-6:])

    messages.append({'role': 'user', 'content': question})

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': 0.3,
                    'num_predict': 512
                }
            },
            timeout=60
        )

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get('message', {}).get('content', 'Cevap alınamadı.')
            return {
                'success': True,
                'answer': answer,
                'model': model
            }
        else:
            return {
                'success': False,
                'answer': f'API hatası: {resp.status_code}',
                'model': model
            }

    except requests.Timeout:
        return {
            'success': False,
            'answer': 'Ollama zaman aşımına uğradı. Model yükleniyor olabilir, tekrar deneyin.',
            'model': model
        }
    except Exception as e:
        return {
            'success': False,
            'answer': f'Bağlantı hatası: {str(e)}',
            'model': model
        }


def get_quick_insights():
    from database import get_kargo_verimlilik, get_yakit_aylik_ozet

    insights = []

    verimlilik = get_kargo_verimlilik()
    if verimlilik:
        en_verimsiz = [v for v in verimlilik if v.get('litre_per_ton') is not None]
        if en_verimsiz:
            insights.append({
                'tip': 'uyari',
                'baslik': 'En Verimsiz Araç',
                'icerik': f"{en_verimsiz[0]['plaka']} - {en_verimsiz[0]['litre_per_ton']:.3f} L/ton"
            })

    aylik = get_yakit_aylik_ozet()
    if len(aylik) >= 2:
        son = aylik[0]
        onceki = aylik[1]
        if onceki['toplam_tutar'] and son['toplam_tutar']:
            degisim = ((son['toplam_tutar'] - onceki['toplam_tutar']) / onceki['toplam_tutar']) * 100
            tip = 'uyari' if degisim > 10 else 'bilgi'
            insights.append({
                'tip': tip,
                'baslik': 'Aylık Maliyet Değişimi',
                'icerik': f"{son['ay']}: {'+' if degisim > 0 else ''}{degisim:.1f}% ({son['toplam_tutar']:.2f}₺)"
            })

    return insights
