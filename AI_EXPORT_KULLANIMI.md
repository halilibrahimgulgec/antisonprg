# AI Asistan Excel/PDF Export Özelliği

AI Asistan artık otomatik olarak Excel ve PDF dosyaları oluşturabilir!

## Nasıl Kullanılır?

### 1. Excel Export
AI Asistan'a şöyle sorular sorun:

- "En fazla yakıt tüketen araçları excel ver"
- "Son yakıt alımlarını excel olarak indir"
- "Bu listeyi excel yap"

AI otomatik olarak:
1. Veritabanından veriyi alır
2. Excel dosyası oluşturur
3. İndirme linki sunar

### 2. PDF Export
Aynı şekilde PDF için:

- "En fazla yakıt tüketen araçları pdf ver"
- "Son yakıt alımlarını pdf olarak indir"
- "Bu listeyi pdf yap"

## Desteklenen Sorgular

AI Asistan şu sorguları Excel/PDF'e çevirebilir:

1. **En Fazla Yakıt Tüketenler**
   - "en fazla yakıt tüketen araçları excel ver"

2. **Son Yakıt Alımları**
   - "son yakıt alımlarını pdf ver"

3. **Plaka Bazlı Sorgular**
   - "46AKH001 plakasının yakıt bilgilerini excel ver"

## Özellikler

- ✅ Otomatik sütun isimleri Türkçeleştirilir
- ✅ Tarih ve saat damgası eklenir
- ✅ Profesyonel formatlama
- ✅ Tek tıkla indirme
- ✅ Butona tıklamaya gerek yok - AI anlıyor!

## Kurulum ve Gereksinimler

### 1. Ollama Model İndirin (ÇOK ÖNEMLİ!)

```bash
ollama pull llama3.2
```

Bu komut Türkçe destekli AI modelini indirir (5-10 dakika sürer).
Model indirilmeden sistem İngilizce konuşur!

### 2. Python Paketleri

Eğer hata alırsanız:

```bash
pip install pandas openpyxl reportlab
```

veya

```bash
pip3 install -r requirements.txt
```

### 3. Uygulamayı Yeniden Başlatın

Model indirdikten sonra:

```bash
# Uygulamayı durdurun (Ctrl + C)
# Sonra yeniden başlatın:
python app.py
```

veya

```bash
baslat.bat
```

## Örnek Kullanım

**Kullanıcı:** "En fazla yakıt tüketen 5 aracı excel ver"

**AI Asistan:**
"Excel dosyası hazırlandı. İndirmek için aşağıdaki linke tıklayın."
[Excel İndir] 📥

İşte bu kadar basit! 🎉
