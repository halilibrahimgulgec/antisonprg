#!/usr/bin/env python3
"""
Sistem Kontrolü ve Teşhis Scripti
ERR_EMPTY_RESPONSE hatasını teşhis eder
"""

import sys
import os
import subprocess
import platform

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_python():
    print_section("PYTHON KONTROLÜ")
    print(f"✅ Python Version: {sys.version}")
    print(f"✅ Python Path: {sys.executable}")
    print(f"✅ Platform: {platform.platform()}")

def check_pip():
    print_section("PIP KONTROLÜ")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Pip: {result.stdout.strip()}")
            return True
        else:
            print("❌ Pip bulunamadı!")
            print("\n📝 ÇÖZÜM:")
            print("Windows: python -m ensurepip --upgrade")
            print("Linux: sudo apt install python3-pip")
            print("Mac: curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py")
            return False
    except Exception as e:
        print(f"❌ Pip kontrol hatası: {e}")
        return False

def check_modules():
    print_section("GEREKLİ MODÜLLER")
    required = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'pandas': 'Pandas',
        'dotenv': 'python-dotenv',
        'sklearn': 'scikit-learn',
        'numpy': 'NumPy',
        'reportlab': 'ReportLab',
        'xlsxwriter': 'XlsxWriter',
        'requests': 'Requests',
        'openpyxl': 'OpenPyXL',
        'werkzeug': 'Werkzeug'
    }

    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - YOK!")
            missing.append(name.lower())

    if missing:
        print("\n📝 EKSİK MODÜLLER YÜKLEMEK İÇİN:")
        print(f"\n{sys.executable} -m pip install {' '.join(missing)}")

    return len(missing) == 0

def check_database():
    print_section("VERİTABANI KONTROLÜ")
    db_path = "kargo_data.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Veritabanı bulundu: {db_path}")
        print(f"   Boyut: {size:,} bytes ({size/1024/1024:.2f} MB)")

        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tablolar: {', '.join([t[0] for t in tables])}")
            conn.close()
        except Exception as e:
            print(f"   ⚠️ Veritabanı okunamadı: {e}")
    else:
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        print("\n📝 ÇÖZÜM: Çalışan PC'den kargo_data.db dosyasını kopyalayın")

def check_files():
    print_section("DOSYA KONTROLÜ")
    required_files = [
        'app.py',
        'database.py',
        'ai_model.py',
        'requirements.txt',
        'templates/index.html'
    ]

    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - YOK!")
            all_exist = False

    return all_exist

def check_port():
    print_section("PORT KONTROLÜ")
    port = 5000
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()

        if result == 0:
            print(f"❌ Port {port} kullanımda!")
            print("\n📝 ÇÖZÜM:")
            print(f"Windows: netstat -ano | findstr :{port}")
            print(f"Linux/Mac: lsof -i :{port}")
            print("Veya app.py'de portu değiştirin (örn: 8080)")
            return False
        else:
            print(f"✅ Port {port} boş")
            return True
    except Exception as e:
        print(f"⚠️ Port kontrolü başarısız: {e}")
        return True

def check_permissions():
    print_section("YETKİ KONTROLÜ")
    try:
        test_file = "test_write_permission.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Yazma yetkisi var")
        return True
    except Exception as e:
        print(f"❌ Yazma yetkisi yok: {e}")
        print("\n📝 ÇÖZÜM: Terminal/CMD'yi admin olarak çalıştırın")
        return False

def generate_install_script():
    print_section("KURULUM SCRİPTİ")

    if platform.system() == "Windows":
        script = """
REM Windows Kurulum Scripti
@echo off
echo Kurulum baslatiliyor...

REM Pip varsa güncelle
python -m ensurepip --upgrade
python -m pip install --upgrade pip

REM Modülleri yükle
python -m pip install flask flask-cors pandas python-dotenv scikit-learn numpy reportlab xlsxwriter requests openpyxl werkzeug

echo.
echo Kurulum tamamlandi!
echo Flask baslatiliyor...
python app.py
pause
"""
        filename = "kurulum.bat"
    else:
        script = """#!/bin/bash
# Linux/Mac Kurulum Scripti
echo "Kurulum baslatiliyor..."

# Pip varsa güncelle
python3 -m pip install --upgrade pip

# Modülleri yükle
python3 -m pip install flask flask-cors pandas python-dotenv scikit-learn numpy reportlab xlsxwriter requests openpyxl werkzeug

echo ""
echo "Kurulum tamamlandi!"
echo "Flask baslatiliyor..."
python3 app.py
"""
        filename = "kurulum.sh"

    with open(filename, 'w') as f:
        f.write(script)

    if platform.system() != "Windows":
        os.chmod(filename, 0o755)

    print(f"✅ Kurulum scripti oluşturuldu: {filename}")
    print(f"\nÇalıştırmak için:")
    if platform.system() == "Windows":
        print(f"   {filename}")
    else:
        print(f"   ./{filename}")

def main():
    print("\n" + "🔍 SİSTEM TEŞHİS ARACI ".center(60, "="))
    print("ERR_EMPTY_RESPONSE Hata Analizi")

    checks = {
        "Python": check_python,
        "Pip": check_pip,
        "Modüller": check_modules,
        "Veritabanı": check_database,
        "Dosyalar": check_files,
        "Port": check_port,
        "Yetkiler": check_permissions
    }

    results = {}
    for name, check_func in checks.items():
        try:
            result = check_func()
            results[name] = result if result is not None else True
        except Exception as e:
            print(f"\n❌ {name} kontrolü başarısız: {e}")
            results[name] = False

    # Özet
    print_section("SONUÇ ÖZETİ")

    all_ok = True
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}: {'OK' if result else 'SORUNLU'}")
        if not result:
            all_ok = False

    print("\n" + "="*60)

    if all_ok:
        print("\n🎉 TÜM KONTROLLER BAŞARILI!")
        print("\nFlask'ı başlatmak için:")
        print(f"   {sys.executable} app.py")
    else:
        print("\n⚠️ SORUNLAR TESPİT EDİLDİ!")
        print("\nYukarıdaki çözümleri uygulayın veya")
        print("otomatik kurulum scriptini çalıştırın.")
        generate_install_script()

    print("\n📚 Detaylı yardım için: KURULUM_REHBERI.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
