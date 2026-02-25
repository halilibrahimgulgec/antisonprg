#!/bin/bash
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
