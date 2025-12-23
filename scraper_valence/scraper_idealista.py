import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service

# -------------------------
# CONFIG SELENIUM FURTIF
# -------------------------

def get_driver():
    ua = UserAgent()

    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={ua.random}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")

    # Headless possible, mais plus risqué :
    # chrome_options.add_argument("--headless=new")


    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# -------------------------
# SCRAPER IDEALISTA
# -------------------------

def scrape_idealista_valencia(pages=5):
    """
    Scrape Idealista (Valence) sur X pages de résultats.
    Retourne un DataFrame.
    """

    driver = get_driver()
    base_url = "https://www.idealista.com/en/venta-viviendas/valencia-valencia/pagina-"

    results = []

    for p in range(1, pages + 1):
        url = base_url + str(p) + ".htm"
        print(f"Scraping: {url}")

        driver.get(url)
        time.sleep(random.uniform(3, 6))  # pause humaine

        ads = driver.find_elements(By.CSS_SELECTOR, ".item-info-container")

        for ad in ads:
            try:
                title = ad.find_element(By.CSS_SELECTOR, ".item-link").text
                link = ad.find_element(By.CSS_SELECTOR, ".item-link").get_attribute("href")

                price_text = ad.find_element(By.CSS_SELECTOR, ".item-price").text
                price = int(price_text.replace("€", "").replace(",", "").replace(".", "").strip())

                details = ad.find_element(By.CSS_SELECTOR, ".item-detail-char").text
                surface = None
                if "m²" in details:
                    surface = float(details.split("m²")[0].split()[-1])

                # Quartier (si visible dans annonce)
                try:
                    barrio = ad.find_element(By.CSS_SELECTOR, ".item-subtitle").text
                except:
                    barrio = ""

                # Aller dans l’annonce pour extraire plus
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(random.uniform(2, 4))

                description = ""
                agency = ""
                coords = ""

                try:
                    description = driver.find_element(By.CSS_SELECTOR, ".comment").text
                except:
                    pass

                try:
                    agency = driver.find_element(By.CSS_SELECTOR, ".about-agency-name").text
                except:
                    pass

                # Récupération des coordonnées lat/lon dans le script JS
                try:
                    scripts = driver.find_elements(By.TAG_NAME, "script")
                    for s in scripts:
                        if "latitude" in s.get_attribute("innerHTML"):
                            txt = s.get_attribute("innerHTML")
                            lat = txt.split("latitude")[1].split(":")[1].split(",")[0].strip()
                            lon = txt.split("longitude")[1].split(":")[1].split(",")[0].strip()
                            coords = f"{lat}, {lon}"
                            break
                except:
                    pass

                # Photos
                photos = []
                try:
                    imgs = driver.find_elements(By.CSS_SELECTOR, ".main-image img")
                    photos = [i.get_attribute("src") for i in imgs]
                except:
                    pass

                # Enregistrer
                results.append({
                    "Titre du bien": title,
                    "Quartier": barrio,
                    "Surface (m²)": surface,
                    "Prix d’achat (€)": price,
                    "Description": description,
                    "Lien annonce": link,
                    "Agence": agency,
                    "Coordonnées": coords,
                    "Photos": photos,
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print("Erreur annonce :", e)
                continue

    driver.quit()
    return pd.DataFrame(results)

# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    df = scrape_idealista_valencia(pages=10)  # → scrape environ 300–500 annonces
    df.to_csv("data/idealista_valencia.csv", index=False)
    print("Terminé. Données sauvegardées.")
