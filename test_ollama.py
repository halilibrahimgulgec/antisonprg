#!/usr/bin/env python3
"""
Ollama AI Asistan Test Script
Bu script Ollama kurulumunu ve çalışmasını test eder
"""

import sys
import requests
import time
from ollama_assistant import OllamaAssistant

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def test_ollama_connection():
    """Ollama servisine bağlantıyı test et"""
    print_header("TEST 1: Ollama Bağlantı Kontrolü")

    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        if response.status_code == 200:
            print_success("Ollama servisi çalışıyor!")
            models = response.json().get('models', [])

            if models:
                print_info(f"Yüklü modeller ({len(models)} adet):")
                for model in models:
                    print(f"  - {model['name']}")
                return True, models
            else:
                print_error("Hiç model yüklü değil!")
                print_info("Şu komutu çalıştırın: ollama pull llama2")
                return False, []
        else:
            print_error(f"Beklenmeyen yanıt: {response.status_code}")
            return False, []

    except requests.exceptions.ConnectionError:
        print_error("Ollama servisine bağlanılamadı!")
        print_info("Çözüm:")
        print_info("  Windows: Başlat menüsünden 'Ollama' uygulamasını açın")
        print_info("  Linux/Mac: Terminal'de 'ollama serve' komutunu çalıştırın")
        return False, []

    except Exception as e:
        print_error(f"Hata: {str(e)}")
        return False, []

def test_assistant_class():
    """OllamaAssistant sınıfını test et"""
    print_header("TEST 2: Assistant Sınıfı Kontrolü")

    try:
        assistant = OllamaAssistant()
        print_success("OllamaAssistant sınıfı başarıyla yüklendi")

        status = assistant.check_ollama_status()
        if status['status'] == 'running':
            print_success("Assistant Ollama'ya bağlanabildi")
            return True
        else:
            print_error("Assistant Ollama'ya bağlanamadı")
            return False

    except Exception as e:
        print_error(f"Assistant sınıfı hatası: {str(e)}")
        return False

def test_simple_query():
    """Basit bir soru sor"""
    print_header("TEST 3: Basit Soru-Cevap Testi")

    try:
        assistant = OllamaAssistant()

        print_info("Soru: 'Merhaba, adın ne?'")
        print_info("Yanıt bekleniyor (30-60 saniye sürebilir)...")

        start_time = time.time()
        result = assistant.ask("Merhaba, adın ne? Kısaca yanıt ver.")
        elapsed_time = time.time() - start_time

        if result['status'] == 'success':
            print_success(f"Yanıt alındı ({elapsed_time:.1f} saniye)")
            print(f"\n📝 Yanıt:\n{result['answer']}\n")
            return True
        else:
            print_error(f"Yanıt alınamadı: {result.get('message')}")
            return False

    except Exception as e:
        print_error(f"Soru-cevap hatası: {str(e)}")
        return False

def test_database_context():
    """Veritabanı bağlamı ile soru sor"""
    print_header("TEST 4: Veritabanı Bağlam Testi")

    try:
        assistant = OllamaAssistant()

        context = assistant.get_context_data()
        print_info("Veritabanı bağlamı alındı:")
        print(context[:200] + "...")

        print_info("\nSoru: 'Sistemde kaç araç var?'")
        print_info("Yanıt bekleniyor...")

        result = assistant.ask_with_db_query("Sistemde kaç araç var? Kısa yanıt ver.")

        if result['status'] == 'success':
            print_success("Bağlam ile yanıt alındı")
            print(f"\n📝 Yanıt:\n{result['answer']}\n")
            return True
        else:
            print_error(f"Yanıt alınamadı: {result.get('message')}")
            return False

    except Exception as e:
        print_error(f"Bağlam testi hatası: {str(e)}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("\n" + "🤖 OLLAMA AI ASISTAN TEST SCRIPT 🤖".center(60))
    print("Bu script Ollama kurulumunuzu test eder\n")

    results = []

    test1, models = test_ollama_connection()
    results.append(("Ollama Bağlantısı", test1))

    if not test1:
        print_header("ÖZET")
        print_error("Ollama servisi çalışmıyor. Diğer testler atlandı.")
        print_info("\nKurulum için OLLAMA_KURULUM.md dosyasını okuyun")
        return

    if not models:
        print_header("ÖZET")
        print_error("Hiç model yüklü değil. Diğer testler atlandı.")
        print_info("\nÖnce bir model indirin: ollama pull llama2")
        return

    test2 = test_assistant_class()
    results.append(("Assistant Sınıfı", test2))

    if test2:
        test3 = test_simple_query()
        results.append(("Basit Soru-Cevap", test3))

        test4 = test_database_context()
        results.append(("Veritabanı Bağlam", test4))

    print_header("TEST SONUÇLARI")
    passed = 0
    failed = 0

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: BAŞARILI")
            passed += 1
        else:
            print_error(f"{test_name}: BAŞARISIZ")
            failed += 1

    print(f"\n📊 Toplam: {passed + failed} test")
    print(f"✅ Başarılı: {passed}")
    print(f"❌ Başarısız: {failed}")

    if failed == 0:
        print_success("\n🎉 Tüm testler başarılı! Sistem hazır.")
        print_info("Şimdi 'python app.py' ile uygulamayı başlatabilirsiniz")
    else:
        print_error("\n⚠️ Bazı testler başarısız oldu.")
        print_info("OLLAMA_KURULUM.md dosyasındaki sorun giderme bölümüne bakın")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test iptal edildi (Ctrl+C)")
        sys.exit(1)
