/*
  # Ana Malzeme Sütunu Ekleme

  1. Değişiklikler
    - `agirlik` tablosuna `ana_malzeme` sütunu ekleniyor
    - Her plaka için en çok taşıdığı malzemeyi otomatik hesaplıyor
    - KUM/BETON/PARKE gibi ana kategorileri işaretliyor
    
  2. Amaç
    - Her kamyonun uzmanlık alanını belirlemek
    - Performans analizini malzeme tipine göre gruplamak
    - Karma araçları ayırt edebilmek
*/

-- Ana malzeme sütununu ekle
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'agirlik' AND column_name = 'ana_malzeme'
  ) THEN
    ALTER TABLE agirlik ADD COLUMN ana_malzeme text;
  END IF;
END $$;

-- Her plaka için ana malzemeyi hesapla ve güncelle
WITH plaka_malzeme_sayisi AS (
    SELECT 
        plaka,
        CASE 
            WHEN birim = 'Kg' THEN 'KUM'
            WHEN birim = 'm3' THEN 'BETON'
            WHEN birim = 'M2' THEN 'PARKE'
            ELSE birim
        END as malzeme,
        COUNT(*) as sefer_sayisi,
        ROW_NUMBER() OVER (PARTITION BY plaka ORDER BY COUNT(*) DESC) as rn
    FROM agirlik
    WHERE miktar IS NOT NULL AND miktar > 0
    GROUP BY plaka, birim
),
ana_malzemeler AS (
    SELECT plaka, malzeme as ana_malzeme
    FROM plaka_malzeme_sayisi
    WHERE rn = 1
)
UPDATE agirlik
SET ana_malzeme = am.ana_malzeme
FROM ana_malzemeler am
WHERE agirlik.plaka = am.plaka;

-- Index ekle (performans için)
CREATE INDEX IF NOT EXISTS idx_agirlik_ana_malzeme ON agirlik(ana_malzeme);
CREATE INDEX IF NOT EXISTS idx_agirlik_plaka_ana_malzeme ON agirlik(plaka, ana_malzeme);
