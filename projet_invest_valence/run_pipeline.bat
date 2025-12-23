@echo off
echo [1/4] Scraping Idealista...
python scraper_idealista.py

echo [2/4] Merge & dedup...
python merge_idealista.py

echo [3/4] Clean & enrich...
python clean_idealista.py

echo [4/4] Fusion + training...
python fusion_dataset.py
python train_model_real.py

echo.
echo ✅ Pipeline complet terminé !
pause