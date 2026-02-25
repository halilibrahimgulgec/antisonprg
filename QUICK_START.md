# Hızlı Başlangıç Rehberi

## ⚠️ ÖNEMLİ: Flask'ı Yeniden Başlatın!

Veritabanı dosya adı değiştirildi. Flask uygulamasını yeniden başlatmanız gerekiyor.

## 🚀 Adım Adım Kullanım

### 1. Veritabanı Oluşturuldu ✅

Örnek verilerle bir veritabanı oluşturuldu:
- **Dosya:** `kargo_data.db`
- **Kayıt Sayısı:** 21 (9 yakıt + 6 ağırlık + 6 araç takip)
- **Plakalar:** 3 farklı araç

### 2. Flask'ı Başlatın

Eğer Flask çalışıyorsa **CTRL+C** ile durdurun, sonra tekrar başlatın:

```bash
python app.py
```

veya

```bash
python3 app.py
```

### 3. Tarayıcıda Açın

```
http://localhost:5000
```

### 4. Veritabanı Durumunu Kontrol Edin

İlk önce şu sayfayı açın:
```
http://localhost:5000/database-status
```

Bu sayfa size:
- ✅ Veritabanı bağlantı durumu
- 📊 Her tabloda kaç kayıt var
- 📈 Toplam istatistikler
- 🔍 Plaka listesi

gösterecek.

### 5. Analiz Yapın

Ana sayfada "📊 Veritabanından Analiz Et" butonuna tıklayın.

## 📋 Kendi Excel Dosyalarınızı Kullanma

Eğer kendi verilerinizi yüklemek istiyorsanız:

1. **ÖNEMLİ: Flask'ı kapatın (CTRL+C)**

2. Excel dosyalarınızı proje klasörüne koyun:
   - `yakit.xlsx` (Yakıt kayıtları)
   - `agirlik.xlsx` veya `kantar.xlsx` (Ağırlık kayıtları)
   - `arac_takip.xlsx` (Araç takip kayıtları)

3. Mevcut veritabanını silin:
```bash
# Windows CMD/PowerShell
del kargo_data.db

# Linux/Mac
rm kargo_data.db
```

4. Excel'den veritabanı oluşturun:
```bash
python excel_to_sqlite.py
```

5. **ÖNEMLİ: Araç Yönetimi tablosunu oluşturun:**
```bash
# Tabloyu oluştur
python create_araclar_table.py

# Mevcut plakaları tabloya ekle
python populate_araclar.py
```

6. Flask'ı yeniden başlatın:
```bash
python app.py
```

## 🔍 Sorun Giderme

### ❌ "database disk image is malformed" Hatası

Veritabanı dosyası bozulmuş. Şunu çalıştırın:

```bash
python fix_database.py
```

Bu komut:
- Bozuk veritabanını siler
- Yeni boş veritabanı oluşturur
- Excel dosyalarınızla veri eklemek için excel_to_sqlite.py kullanın

### Hala "Veritabanında veri yok" hatası alıyorsanız:

1. **Flask'ı yeniden başlattınız mı?** CTRL+C ile durdurup tekrar başlatın
2. **Veritabanı var mı?** `ls -la kargo_data.db` ile kontrol edin
3. **Tarayıcı cache'i** temizleyin (CTRL+SHIFT+R veya CTRL+F5)
4. **Debug endpoint'ini** kontrol edin: http://localhost:5000/debug-info

### Manuel Veritabanı Kontrolü

Terminal'de:
```bash
python3 -c "from database import get_database_info, get_statistics; import json; print(json.dumps(get_database_info(), indent=2)); print(json.dumps(get_statistics(), indent=2))"
```

### Veritabanı Sıfırlama

Eğer bir şeyler ters gittiyse:
```bash
rm kargo_data.db
python3 -c "import sqlite3; conn = sqlite3.connect('kargo_data.db'); ... # Tablolar oluşturulur"
```

Veya yukarıdaki "Örnek veri oluşturma" scriptini tekrar çalıştırın.

## 📊 Örnek Veri İçeriği

Oluşturulan veritabanında:
- **3 Plaka:** 34 ABC 123, 06 XYZ 456, 35 DEF 789
- **Her plaka için:**
  - 3 yakıt kaydı (~150-170 litre)
  - 2 ağırlık kaydı (~25 ton)
  - 2 araç takip kaydı (~450-500 km)

## 🎯 Beklenen Sonuç

Ana sayfada:
- ✅ Yeşil "Veritabanı Bağlantısı Başarılı" mesajı
- 📁 Dosya: `kargo_data.db`
- 📊 Tablo bilgileri (yakit: 9, agirlik: 6, arac_takip: 6)

Analiz sonrası:
- 📈 3 araç için grafik
- 🔥 Toplam yakıt: ~1445 litre
- 💰 Toplam maliyet: ~46,946 ₺

## 💡 Önemli Notlar

1. **Dosya adı `kargo_data.db` olmalı** (`kargo_database.db` değil!)
2. **Flask her değişiklikten sonra yeniden başlatılmalı**
3. **Veritabanı dosyası Git'e eklenmez** (.gitignore'da)
4. **Excel dosyaları opsiyonel** (örnek veri hazır)

## 🆘 Yardım

Hala sorun mu yaşıyorsunuz?

1. `/database-status` sayfasını açın
2. Terminal'deki Flask loglarını kontrol edin
3. Tarayıcı konsolu hatalarını kontrol edin (F12)
4. `debug-info` endpoint'ini kontrol edin
