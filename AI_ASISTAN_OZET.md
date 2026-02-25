# 🤖 AI Asistan Hızlı Başlangıç

## Ne Yaptık?

Projenize **yerelde çalışan** bir AI asistan ekledik. Bu asistan:

- ✅ Tüm sorularınızı yanıtlayabilir
- ✅ Veritabanınızdaki verilere erişebilir
- ✅ Tamamen **yerelde çalışır** (internet gerektirmez)
- ✅ Verileriniz güvende kalır
- ✅ Ücretsiz ve açık kaynak

## Hızlı Kurulum (3 Adım)

### 1. Ollama'yı İndirin

**Windows:**
- [ollama.ai/download/windows](https://ollama.ai/download/windows) adresinden indirin
- Kurulumu tamamlayın

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
- [ollama.ai/download/mac](https://ollama.ai/download/mac) adresinden indirin
- Kurulumu tamamlayın

### 2. Model İndirin

```bash
ollama pull llama2
```

Bu işlem 5-15 dakika sürebilir (model 4GB).

### 3. Test Edin

```bash
python test_ollama.py
```

## Kullanım

1. Uygulamayı başlatın: `python app.py`
2. Tarayıcıda açın: `http://localhost:5000`
3. **"🤖 AI Asistan"** butonuna tıklayın
4. Soru sorun!

## Örnek Sorular

- "En fazla yakıt tüketen araçlar hangileri?"
- "Son yakıt alımlarını göster"
- "Sistemde kaç aktif araç var?"
- "Bugün ne yapmalıyım?"
- "34ABC123 plakası hakkında bilgi ver"
- "Bu ay toplam yakıt tüketimi ne kadar?"

## Önemli Notlar

- **İnternet bağlantısı gerektirmez** (model indirme hariç)
- **API key gerektirmez**
- **Ücretsiz**
- **Verileriniz dışarı çıkmaz**
- İlk sorgular yavaş olabilir (30-60 saniye), sonrakiler hızlanır

## Sorun mu Yaşıyorsunuz?

Detaylı kurulum ve sorun giderme için:
👉 **[OLLAMA_KURULUM.md](OLLAMA_KURULUM.md)** dosyasına bakın

## Sistem Gereksinimleri

**Minimum:**
- RAM: 8 GB
- Disk: 5 GB boş alan
- İşlemci: 4 çekirdek

**Önerilen:**
- RAM: 16 GB
- Disk: 10 GB boş alan
- İşlemci: 8 çekirdek

## Alternatif Modeller

Daha hızlı yanıt için:
```bash
ollama pull mistral
```

Daha güçlü model için:
```bash
ollama pull llama2:13b
```

## Destek

- Test script: `python test_ollama.py`
- Detaylı dokümantasyon: `OLLAMA_KURULUM.md`
- Ollama dokümantasyon: [ollama.ai/docs](https://ollama.ai/docs)

---

**Hazırsınız! Asistanınız sorularınızı bekliyor.** 🚀
