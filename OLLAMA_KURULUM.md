# Ollama AI Asistan Kurulum Rehberi

## 1. Ollama Nedir?

Ollama, bilgisayarınızda **yerelde** çalışan açık kaynak yapay zeka modellerini kullanmanızı sağlar. İnternet bağlantısı gerektirmez, verileriniz tamamen güvende kalır.

## 2. Ollama Kurulumu

### Windows için:

1. [Ollama Windows İndirme Sayfası](https://ollama.ai/download/windows) adresine gidin
2. `OllamaSetup.exe` dosyasını indirin
3. İndirilen dosyayı çalıştırın ve kurulumu tamamlayın
4. Kurulum tamamlandıktan sonra Ollama otomatik olarak başlayacaktır

### Linux için:

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### macOS için:

1. [Ollama macOS İndirme Sayfası](https://ollama.ai/download/mac) adresine gidin
2. `.dmg` dosyasını indirin
3. Uygulamayı Applications klasörüne sürükleyin

## 3. Model İndirme

Ollama kurulduktan sonra, AI modelini indirmeniz gerekiyor:

### Önerilen Model: Llama 2 (Türkçe destekli)

```bash
ollama pull llama2
```

### Alternatif Modeller:

#### Daha küçük ve hızlı (Düşük sistem gereksinimleri):
```bash
ollama pull mistral
```

#### Daha güçlü (Yüksek sistem gereksinimleri):
```bash
ollama pull llama2:13b
```

#### Kod odaklı:
```bash
ollama pull codellama
```

## 4. Ollama Servisini Başlatma

### Windows:
Ollama otomatik olarak başlar. Sistem tepsisinde Ollama simgesini görebilirsiniz.

### Linux/macOS:
```bash
ollama serve
```

## 5. Ollama Durumunu Kontrol Etme

Terminal/CMD'de aşağıdaki komutu çalıştırın:

```bash
ollama list
```

Bu komut indirdiğiniz modelleri gösterir.

## 6. Projenin Gereksinimlerini Yükleme

```bash
pip install -r requirements.txt
```

## 7. Uygulamayı Başlatma

```bash
python app.py
```

Tarayıcınızda şu adrese gidin:
```
http://localhost:5000/ai-assistant
```

## 8. AI Asistan Kullanımı

1. **Ana Sayfadan**: "🤖 AI Asistan" butonuna tıklayın
2. **Durum Kontrolü**: Sayfanın sağ üst köşesinde yeşil nokta Ollama'nın çalıştığını gösterir
3. **Soru Sorma**:
   - Hızlı soru butonlarından birini seçin
   - Veya kendi sorunuzu yazın
4. **Örnek Sorular**:
   - "En fazla yakıt tüketen araçlar hangileri?"
   - "Son yakıt alımlarını göster"
   - "Sistemde kaç aktif araç var?"
   - "Bugün yapılması gerekenler neler?"

## 9. Sorun Giderme

### Ollama çalışmıyor:

**Windows:**
1. Görev Yöneticisi'ni açın
2. "Ollama" servisini arayın
3. Çalışmıyorsa, başlat menüsünden "Ollama" uygulamasını açın

**Linux/macOS:**
```bash
# Servisi başlat
ollama serve

# Veya arka planda çalıştır
nohup ollama serve &
```

### Model yavaş yanıt veriyor:

- Daha küçük bir model kullanın: `ollama pull mistral`
- Sistem kaynaklarını kontrol edin (RAM, CPU)
- Diğer uygulamaları kapatın

### "Bağlantı hatası" alıyorum:

1. Ollama servisinin çalıştığından emin olun:
```bash
curl http://localhost:11434/api/tags
```

2. Firewall ayarlarını kontrol edin
3. Port 11434'ün kullanımda olmadığını kontrol edin

### Model bulunamadı hatası:

```bash
# Modeli tekrar indirin
ollama pull llama2

# Mevcut modelleri kontrol edin
ollama list
```

## 10. Sistem Gereksinimleri

### Minimum:
- **RAM**: 8 GB
- **Disk**: 4 GB boş alan
- **İşlemci**: 4 çekirdek

### Önerilen:
- **RAM**: 16 GB
- **Disk**: 10 GB boş alan
- **İşlemci**: 8 çekirdek
- **GPU**: NVIDIA (opsiyonel, hızlandırma için)

## 11. Model Boyutları

| Model | Boyut | RAM Gereksinimi |
|-------|-------|-----------------|
| llama2 | ~4 GB | 8 GB |
| llama2:13b | ~7 GB | 16 GB |
| mistral | ~4 GB | 8 GB |
| codellama | ~4 GB | 8 GB |

## 12. Ek Özellikler

### Model Değiştirme:

`ollama_assistant.py` dosyasında:

```python
assistant = OllamaAssistant(model='mistral')  # llama2 yerine mistral
```

### Farklı Port Kullanma:

```python
assistant = OllamaAssistant(base_url='http://localhost:8080')
```

## 13. Güvenlik

- Tüm veriler **yerelde** işlenir
- İnternet bağlantısı gerektirmez
- Verileriniz dışarı çıkmaz
- API key veya hesap gerektirmez

## 14. Performans İyileştirme

1. **GPU Desteği** (NVIDIA):
   ```bash
   # CUDA kurulu olduğundan emin olun
   nvidia-smi
   ```

2. **CPU Çekirdek Sayısını Artırma**:
   ```bash
   export OLLAMA_NUM_THREAD=8
   ```

3. **Context Boyutu Ayarlama**:
   ```bash
   export OLLAMA_CONTEXT_SIZE=4096
   ```

## Destek

Sorun yaşıyorsanız:
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Dokümantasyon](https://ollama.ai/docs)

---

**Not**: İlk model indirme işlemi internet hızınıza bağlı olarak 5-15 dakika sürebilir.
