import re
import os

translations = {
    'en': {
        'Toplam Kayıt': 'Total Records',
        'Yakıt Kayıtları': 'Fuel Records',
        'Ağırlık Kayıtları': 'Weight Records',
        'Araç Takip': 'Vehicle Tracking',
        'Toplam Plaka': 'Total Plates',
        'Toplam Motorin': 'Total Diesel',
        'Toplam AdBlue': 'Total AdBlue',
        'Kargo Araçları Analizi': 'Cargo Vehicles Analysis',
        'Binek Araç Analizi': 'Passenger Cars Analysis',
        'İş Makinesi Analizi': 'Heavy Machinery Analysis',
        'Muhasebe Analizi': 'Accounting Analysis',
        'AI Analiz': 'AI Analysis',
        'Araç Yönetimi': 'Vehicle Management',
        'Araç Bakım': 'Vehicle Maintenance',
        'Bakım Analiz Paneli': 'Maintenance Analysis Panel',
        'Şoför Yönetimi': 'Driver Management',
        'Hasar ve Ceza Yönetimi': 'Damage & Fine Management',
        'Lastik Yönetimi': 'Tire Management',
        'AI Asistan - Sorularınızı Yanıtlar': 'AI Assistant - Answers Your Questions',
        'Mobil Şoför Paneli (PWA)': 'Mobile Driver Panel (PWA)',
        'Saha Bildirim Merkezi (Gelen Kutusu)': 'Field Notification Center (Inbox)',
        'Veri Yükleme': 'Data Upload',
        'Otomatik Veri Çekme': 'Automatic Data Extraction',
        'Ayarlar': 'Settings',
        'Tanımlı mail adresinden gelen Excel dosyalarını otomatik olarak indirip işler.': 'Automatically downloads and processes Excel files from defined email address.',
        'Mailden Verileri Çek': 'Fetch Data from Mail',
        'Mail Ayarları': 'Mail Settings',
        'Gmail Adresi:': 'Gmail Address:',
        'Uygulama Şifresi:': 'App Password:',
        'Gmail &gt; Güvenlik &gt; Uygulama Şifreleri (Normal şifreniz DEĞİL)': 'Gmail &gt; Security &gt; App Passwords (NOT your normal password)',
        'Gönderici Filtresi (Opsiyonel):': 'Sender Filter (Optional):',
        'Virgül ile ayırarak birden fazla mail ekleyebilirsiniz.': 'You can add multiple emails separated by commas.',
        'İptal': 'Cancel',
        'Kaydet': 'Save',
        'Motorin / Yakıt Excel Dosyası': 'Diesel / Fuel Excel File',
        'Kantar Excel Dosyası': 'Weighbridge Excel File',
        'Araç Takip Raporu': 'Vehicle Tracking Report',
        'Dosyaları Yükle ve İşle': 'Upload and Process Files',
        'Desteklenen formatlar: .xlsx, .xls, .csv': 'Supported formats: .xlsx, .xls, .csv',
        'BİNEK ARAÇ': 'PASSENGER CAR',
        'İŞ MAKİNESİ': 'HEAVY MACHINERY',
        'KARGO ARACI': 'CARGO VEHICLE',
        'Kargo Araçları': 'Cargo Vehicles',
        'Binek Araçları': 'Passenger Cars',
        'İş Makineleri': 'Heavy Machinery',
        'BİZİM': 'OWNED',
        'TAŞERON': 'SUBCONTRACTOR'
    },
    'de': {
        'Toplam Kayıt': 'Gesamtdatensätze',
        'Yakıt Kayıtları': 'Kraftstoffaufzeichnungen',
        'Ağırlık Kayıtları': 'Gewichtsaufzeichnungen',
        'Araç Takip': 'Fahrzeugortung',
        'Toplam Plaka': 'Gesamtzahl der Kennzeichen',
        'Toplam Motorin': 'Gesamt Diesel',
        'Toplam AdBlue': 'Gesamt AdBlue',
        'Kargo Araçları Analizi': 'Frachtfahrzeug-Analyse',
        'Binek Araç Analizi': 'PKW-Analyse',
        'İş Makinesi Analizi': 'Baumaschinen-Analyse',
        'Muhasebe Analizi': 'Buchhaltungsanalyse',
        'AI Analiz': 'KI-Analyse',
        'Araç Yönetimi': 'Fahrzeugverwaltung',
        'Araç Bakım': 'Fahrzeugwartung',
        'Bakım Analiz Paneli': 'Wartungsanalyse-Panel',
        'Şoför Yönetimi': 'Fahrerverwaltung',
        'Hasar ve Ceza Yönetimi': 'Schadens- und Strafenverwaltung',
        'Lastik Yönetimi': 'Reifenverwaltung',
        'AI Asistan - Sorularınızı Yanıtlar': 'KI-Assistent - Beantwortet Ihre Fragen',
        'Mobil Şoför Paneli (PWA)': 'Mobiles Fahrer-Panel (PWA)',
        'Saha Bildirim Merkezi (Gelen Kutusu)': 'Feld-Benachrichtigungszentrum (Posteingang)',
        'Veri Yükleme': 'Daten-Upload',
        'Otomatik Veri Çekme': 'Automatische Datenextraktion',
        'Ayarlar': 'Einstellungen',
        'Tanımlı mail adresinden gelen Excel dosyalarını otomatik olarak indirip işler.': 'Lädt automatisch Excel-Dateien von der definierten E-Mail-Adresse herunter und verarbeitet sie.',
        'Mailden Verileri Çek': 'Daten aus E-Mail abrufen',
        'Mail Ayarları': 'E-Mail-Einstellungen',
        'Gmail Adresi:': 'Gmail-Adresse:',
        'Uygulama Şifresi:': 'App-Passwort:',
        'Gmail &gt; Güvenlik &gt; Uygulama Şifreleri (Normal şifreniz DEĞİL)': 'Gmail &gt; Sicherheit &gt; App-Passwörter (NICHT Ihr normales Passwort)',
        'Gönderici Filtresi (Opsiyonel):': 'Absenderfilter (Optional):',
        'Virgül ile ayırarak birden fazla mail ekleyebilirsiniz.': 'Sie können mehrere E-Mails durch Kommas getrennt hinzufügen.',
        'İptal': 'Abbrechen',
        'Kaydet': 'Speichern',
        'Motorin / Yakıt Excel Dosyası': 'Diesel / Kraftstoff Excel-Datei',
        'Kantar Excel Dosyası': 'Waagen Excel-Datei',
        'Araç Takip Raporu': 'Fahrzeugortungsbericht',
        'Dosyaları Yükle ve İşle': 'Dateien hochladen und verarbeiten',
        'Desteklenen formatlar: .xlsx, .xls, .csv': 'Unterstützte Formate: .xlsx, .xls, .csv',
        'BİNEK ARAÇ': 'PKW',
        'İŞ MAKİNESİ': 'BAUMASCHINE',
        'KARGO ARACI': 'FRACHTFAHRZEUG',
        'Kargo Araçları': 'Frachtfahrzeuge',
        'Binek Araçları': 'PKWs',
        'İş Makineleri': 'Baumaschinen',
        'BİZİM': 'EIGEN',
        'TAŞERON': 'SUBUNTERNEHMER'
    }
}

base_dir = r"c:\Users\User\Desktop\boltson12112025_1\project\translations"

for lang in ['en', 'de']:
    po_file = os.path.join(base_dir, lang, "LC_MESSAGES", "messages.po")
    with open(po_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    blocks = content.split('\n\n')
    new_blocks = []
    
    for block in blocks:
        if block.strip() == '':
            continue
            
        msgid_match = re.search(r'msgid "(.*)"', block)
        if msgid_match:
            msgid = msgid_match.group(1)
            # Find if msgstr is empty
            if 'msgstr ""' in block and msgid in translations[lang]:
                translated_text = translations[lang][msgid]
                block = block.replace('msgstr ""', f'msgstr "{translated_text}"')
        new_blocks.append(block)
        
    with open(po_file, "w", encoding="utf-8") as f:
        f.write('\n\n'.join(new_blocks) + '\n\n')
print("Translation update complete.")
