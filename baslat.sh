#!/bin/bash

echo "=========================================="
echo "YAKIT TAHMIN SISTEMI BASLATILIYOR..."
echo "=========================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[HATA] Python3 bulunamadı!${NC}"
    echo "Python 3.8+ yükleyin: https://python.org"
    exit 1
fi

echo -e "${GREEN}[OK] Python bulundu${NC}"
echo ""

# Sanal ortam kontrolü
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[BILGI] Sanal ortam oluşturuluyor...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[HATA] Sanal ortam oluşturulamadı!${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Sanal ortam oluşturuldu${NC}"
    echo ""
fi

# Sanal ortamı aktif et
echo -e "${YELLOW}[BILGI] Sanal ortam aktif ediliyor...${NC}"
source venv/bin/activate

# Bağımlılık kontrolü
if ! pip show flask &> /dev/null; then
    echo -e "${YELLOW}[BILGI] Bağımlılıklar yükleniyor...${NC}"
    echo "Bu işlem biraz zaman alabilir..."
    echo ""
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}[HATA] Bağımlılıklar yüklenemedi!${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Bağımlılıklar yüklendi${NC}"
    echo ""
fi

# Veritabanı kontrolü
if [ ! -f "kargo_data.db" ]; then
    echo -e "${YELLOW}[UYARI] kargo_data.db bulunamadı!${NC}"
    echo "Excel dosyası yükleyerek veritabanı oluşturabilirsiniz."
    echo ""
fi

# Port temizle (5000)
echo -e "${YELLOW}[BILGI] Port 5000 temizleniyor...${NC}"
lsof -ti:5000 | xargs kill -9 2>/dev/null

echo ""
echo "=========================================="
echo "FLASK UYGULAMASI BASLATILIYOR..."
echo "=========================================="
echo ""
echo -e "${GREEN}Tarayıcınızda şu adresi açın:${NC}"
echo -e "${GREEN}http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}Uygulamayı durdurmak için CTRL+C basın${NC}"
echo ""
echo "=========================================="
echo ""

# Flask'i başlat
python3 app.py
