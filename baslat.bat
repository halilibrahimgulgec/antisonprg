@echo off
echo ==========================================
echo YAKIT TAHMIN SISTEMI BASLATILIYOR...
echo ==========================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python 3.8+ yukleyin: https://python.org
    pause
    exit /b 1
)

echo [OK] Python bulundu
echo.

REM Sanal ortam kontrolu
if not exist "venv\" (
    echo [BILGI] Sanal ortam olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
    echo [OK] Sanal ortam olusturuldu
    echo.
)

REM Sanal ortami aktif et
echo [BILGI] Sanal ortam aktif ediliyor...
call venv\Scripts\activate.bat

REM Bagimlilik kontrolu
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [BILGI] Bagimliliklari yukleniyor...
    echo Bu islem biraz zaman alabilir...
    echo.
    pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [HATA] Bagimliliklari yuklenemedi!
        pause
        exit /b 1
    )
    echo [OK] Bagimliliklari yuklendi
    echo.
)

REM Veritabani kontrolu
if not exist "kargo_data.db" (
    echo [UYARI] kargo_data.db bulunamadi!
    echo Excel dosyasi yukleyerek veritabani olusturabilirsiniz.
    echo.
)

REM Port temizle (5000)
echo [BILGI] Port 5000 temizleniyor...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ==========================================
echo FLASK UYGULAMASI BASLATILIYOR...
echo ==========================================
echo.
echo Tarayicinizda su adresi acin:
echo http://localhost:5000
echo.
echo Uygulamayi durdurmak icin CTRL+C basin
echo.
echo ==========================================
echo.

REM Flask'i baslat
python app.py

pause
