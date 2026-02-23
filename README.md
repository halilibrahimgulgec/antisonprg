# 🚛 Kargo Yakıt Tahmin Sistemi

SQLite veritabanı tabanlı yakıt tüketimi analiz ve tahmin sistemi.

## ⚡ HIZLI BAŞLANGIÇ (TEK TIK!)

### 🪟 Windows Kullanıcıları
```cmd
baslat.bat
```
**Dosyaya çift tıkla!** Tarayıcında `http://localhost:5000` aç! ✅

### 🐧 Linux/Mac Kullanıcıları
```bash
chmod +x baslat.sh
./baslat.sh
```
Tarayıcında `http://localhost:5000` aç! ✅

---

## ❗ SORUN GİDERME

**ERR_EMPTY_RESPONSE hatası alıyorsan:**

👉 **[KURULUM_REHBERI.md](KURULUM_REHBERI.md)** dosyasını aç ve adım adım takip et!

**Hızlı Çözümler:**

1️⃣ **Bağımlılıkları yükle:**
```bash
pip install -r requirements.txt
```

2️⃣ **Port değiştir:**
`app.py` son satırını düzenle → `port=8080` yap

3️⃣ **Veritabanını kopyala:**
Çalışan PC'den `kargo_data.db` dosyasını kopyala

---

## 📋 Özellikler

- ✅ **Kargo Araçları Analizi** - Tonaj ve yakıt tüketimi
- 🚗 **Binek Araç Analizi** - Yakıt performansı
- 🚜 **İş Makinesi Analizi** - Operasyon verimliliği
- 📊 **Tarih & Plaka Filtreleme** - Her sayfada özel filtreler
- 📈 **AI Tahmin Sistemi** - Yapay zeka destekli analizler
- 📈 **Grafik Gösterimi** - Chart.js ile interaktif grafikler
- 🤖 **YENİ: AI Asistan** - Yerelde çalışan Ollama LLM ile sorularınızı yanıtlar!
- 🗄️ **SQLite Veritabanı** - Yerel, hızlı ve güvenli veri saklama
- 💾 **Excel/PDF Export** - Raporları indir
- 🔍 **Veritabanı Durumu** - Anlık durum kontrolü ve debugging

---

## 🚀 Manuel Kurulum

### 1. Gereksinimleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Veritabanı Oluşturun

**Boş veritabanı oluştur:**
```bash
python fix_database.py
```

**Excel verilerini yükle:**
```bash
# 1. Flask çalışıyorsa KAPAT (CTRL+C)
# 2. Excel dosyalarınızı proje klasörüne koyun
# 3. Bu komutu çalıştır:
python excel_to_sqlite.py
```

**ÖNEMLI: Araç Yönetimi Tablosunu Oluşturun:**
```bash
# 1. Araç yönetimi tablosunu oluştur
python create_araclar_table.py

# 2. Mevcut plakaları tabloya ekle (otomatik)
python populate_araclar.py
```

Bu adımlar ZORUNLUDUR! Araç yönetimi ve performans analizi özellikleri bu tabloya bağımlıdır.
Tüm mevcut plakalar otomatik olarak "BİZİM" ve "KARGO ARACI" olarak eklenir.

### 3. Flask'ı Başlatın

```bash
python app.py
```

### 4. Tarayıcıda Açın

```
http://localhost:5000
```

## 📁 Dosya Yapısı

```
project/
├── app.py                      # Ana Flask uygulaması (basitleştirilmiş)
├── database.py                 # SQLite veritabanı fonksiyonları
├── model_analyzer.py           # Veri analiz modülü
├── ai_model.py                 # AI tahmin modelleri
├── ollama_assistant.py         # 🤖 YENİ: Ollama AI Asistan
├── excel_to_sqlite.py          # Excel → SQLite aktarım
├── requirements.txt            # Python bağımlılıkları
├── kargo_data.db              # SQLite veritabanı
├── QUICK_START.md             # Detaylı kullanım rehberi
├── OLLAMA_KURULUM.md          # 🤖 YENİ: Ollama kurulum rehberi
├── test_ollama.py             # 🤖 YENİ: Ollama test scripti
├── README.md                  # Bu dosya
└── templates/
    ├── index.html             # Ana sayfa
    ├── ai_assistant.html      # 🤖 YENİ: AI Asistan sayfası
    ├── muhasebe.html          # Muhasebe sayfası
    ├── result.html            # Yakıt analiz sonuçları
    ├── muhasebe_result.html   # Muhasebe sonuçları
    └── database_status.html   # Veritabanı durum sayfası
```

## 🎯 Kullanım

### Ana Sayfa (/)
- Veritabanı bağlantı durumu
- "Veritabanından Analiz Et" butonu
- Plaka bazlı yakıt tüketimleri

### 🤖 YENİ: AI Asistan (/ai-assistant)
- **Yerelde çalışan** Ollama LLM ile sorularınızı yanıtlar
- Veritabanı verilerine erişim
- Doğal dil ile soru sorma
- Sohbet geçmişi
- **Kurulum**: [OLLAMA_KURULUM.md](OLLAMA_KURULUM.md) dosyasına bakın
- **Test**: `python test_ollama.py` komutu ile test edin

### Muhasebe Sayfası (/muhasebe)
- Maliyet analizi
- Bütçe takibi
- Grafik gösterimi

### Veritabanı Durumu (/database-status)
- Tablo bilgileri
- Kayıt sayıları
- İstatistikler
- Debug bilgileri

## 📊 Veritabanı Yapısı

### Tablolar

**yakit** - Yakıt kayıtları
- plaka, islem_tarihi, yakit_miktari, birim_fiyat, satir_tutari, km_bilgisi

**agirlik** - Kantar kayıtları
- plaka, tarih, miktar, net_agirlik, cari_adi

**arac_takip** - GPS takip kayıtları
- plaka, tarih, toplam_kilometre, hareket_suresi, gunluk_yakit_tuketimi_l

## 🔧 Önemli Notlar

1. **Veritabanı dosyası:** `kargo_data.db` (tek dosya, kolay yedekleme)
2. **Flask her değişiklikten sonra yeniden başlatılmalı**
3. **Tarayıcı cache:** CTRL+SHIFT+R ile temizleyin
4. **Excel formatı:** Standart sütun adları gerekli

## 🛠️ Sorun Giderme

### Veritabanı Bulunamadı

```bash
python excel_to_sqlite.py
```

### Tablo Yok Hatası

```bash
rm kargo_data.db
python excel_to_sqlite.py
```

### Port 5000 Kullanımda

`app.py` dosyasında portu değiştirin:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

## 📚 API Endpoints

- `GET /` - Ana sayfa
- `POST /upload` - Veritabanından analiz
- `GET /muhasebe` - Muhasebe sayfası
- `POST /muhasebe-upload` - Muhasebe analizi
- `GET /database-status` - Veritabanı durumu (HTML)
- `GET /debug-info` - Debug bilgisi (JSON)

## 🔒 Güvenlik

- Veritabanı yerel (bilgisayarınızda)
- Internet bağlantısı gerektirmez
- Veriler güvenli SQLite formatında
- Secret key değiştirilebilir (`app.py`)

## 💾 Yedekleme

```bash
cp kargo_data.db kargo_data_backup_$(date +%Y%m%d).db
```

## 📝 Gereksinimler

- Python 3.8+
- Flask
- Pandas
- SQLite3 (Python ile gelir)
- Flask-CORS

## 🎓 Daha Fazla Bilgi

Detaylı kullanım ve sorun giderme için:
```
QUICK_START.md
```

## 📄 Lisans

Bu proje kargo şirketi için özel olarak geliştirilmiştir.

---

**Son Güncelleme:** 12 Ekim 2025
**Versiyon:** 2.0 (Basitleştirilmiş)
"# antisonprg" 
