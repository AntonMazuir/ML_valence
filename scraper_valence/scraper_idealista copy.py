import time
from datetime import datetime
import random
import pandas as pd
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException




def is_captcha_page(driver, context=None):
    """
    context : 
        - "listing" pour une page de résultats
        - "detail" pour une page d'annonce
        - None si tu t'en fous
    """
    try:
        # 1) Cas classique : reCAPTCHA / iframe dédiée
        if driver.find_elements(By.CSS_SELECTOR, "iframe[src*='captcha'], iframe[src*='recaptcha'], div.g-recaptcha"):
            return True

        # 2) Éléments avec id/class qui contiennent 'captcha'
        captcha_like = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(@id, 'CAPTCHA', 'captcha'), 'captcha') or "
            "contains(translate(@class, 'CAPTCHA', 'captcha'), 'captcha')]"
        )
        if captcha_like:
            # On ajoute une vérif de contexte pour éviter les faux positifs
            if context == "listing":
                # S'il n'y a plus aucune annonce, c'est probablement un mur
                ads = driver.find_elements(By.CSS_SELECTOR, ".item-info-container")
                if len(ads) == 0:
                    return True
            elif context == "detail":
                # Sur la page d'annonce, on s'attend à trouver le bloc d'infos
                main_infos = driver.find_elements(By.CSS_SELECTOR, ".main-info")
                if len(main_infos) == 0:
                    return True
            else:
                # Pas de contexte → on considère que c'est un captcha
                return True

        return False

    except Exception:
        # En cas de doute, on retourne False pour ne pas tout bloquer
        return False

def handle_captcha_manually(driver):
    """
    Met le script en pause le temps que tu résolves le CAPTCHA.
    """
    while True:
        print("⚠️ CAPTCHA détecté.")
        input("➡ Résous le CAPTCHA dans la fenêtre du navigateur, puis appuie sur Entrée ici pour continuer... ")

        # On laisse 2 secondes au navigateur pour recharger après validation
        time.sleep(2)

        if not is_captcha_page(driver):
            print("✅ CAPTCHA résolu, reprise du scraping.")
            break
        else:
            print("⚠️ Le CAPTCHA est toujours présent, réessaie puis ré-appuie sur Entrée.")



# -------------------------
# PAUSES & SCROLL HUMAIN
# -------------------------

def human_wait(min_s=0.8, max_s=2.5):
    """Pause avec durée aléatoire réaliste."""
    time.sleep(random.uniform(min_s, max_s))

def human_scroll(driver):
    """Scroll humain : en plusieurs étapes, avec petites pauses."""
    height = driver.execute_script("return document.body.scrollHeight")
    steps = random.randint(3, 6)
    for i in range(steps):
        # position de scroll entre 0.2 et 1.0 de la page
        position = (i + 1) / steps * random.uniform(0.6, 1.0)
        driver.execute_script(f"window.scrollTo(0, {position} * {height});")
        human_wait(0.4, 1.2)

    # remonter un peu (comportement humain)
    if random.random() < 0.5:
        driver.execute_script("window.scrollTo(0, 0);")
        human_wait(0.4, 1.0)

# -------------------------
# CONFIG SELENIUM FURTIF
# -------------------------

def get_driver():
    chrome_options = uc.ChromeOptions()

    # --- User-agent réaliste ---
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
    ]
    ua = random.choice(USER_AGENTS)
    chrome_options.add_argument(f"--user-agent={ua}")

    # --- Flags anti-détection ---
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")

    # Headless possible mais plus risqué :
    # chrome_options.headless = True

    # --- Langage & locale ---
    chrome_options.add_argument("--lang=es-ES,es")
    chrome_options.add_argument("--accept-lang=es-ES,es")

    driver = uc.Chrome(options=chrome_options)

    # --- Headers supplémentaires via CDP ---
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Accept-Language": "es-ES,es;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        }
    })

    # --- Script JS anti-fingerprint Selenium ---
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-ES', 'es']
                });
            """
        },
    )

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
    # ⚠️ version espagnole (sans /en/)
    base_url = "https://www.idealista.com/venta-viviendas/valencia-valencia/pagina-"

    results = []

    for p in range(1, pages + 1):
        url = base_url + str(p) + ".htm"
        print(f"Scraping: {url}")

        driver.get(url)
        human_wait(2.5, 5.0)

        # 🔹 Gestion CAPTCHA sur la page de listing
        if is_captcha_page(driver, context="listing"):
            handle_captcha_manually(driver)
        if is_captcha_page(driver, context="listing"):
            print("🚫 Impossible de passer le CAPTCHA sur la page de listing, arrêt du scraping.")
            break


        human_scroll(driver)

        ads = driver.find_elements(By.CSS_SELECTOR, ".item-info-container")
        print(f"  → {len(ads)} annonces trouvées sur la page {p}")

        for ad in ads:
            try:
                human_wait(0.6, 1.5)

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
                human_wait(2.0, 4.0)

                 # 🔹 Gestion CAPTCHA sur la page d’annonce
                if is_captcha_page(driver, context="detail"):
                    handle_captcha_manually(driver)
                    if is_captcha_page(driver, context="detail"):
                        print("🚫 Impossible de passer le CAPTCHA sur l’annonce, on skip.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                human_scroll(driver)

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
                        inner = s.get_attribute("innerHTML")
                        if "latitude" in inner and "longitude" in inner:
                            lat = inner.split("latitude")[1].split(":")[1].split(",")[0].strip()
                            lon = inner.split("longitude")[1].split(":")[1].split(",")[0].strip()
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
                    "Date scraping": datetime.now().strftime("%Y-%m-%d")
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print("Erreur annonce :", e)
                try:
                    # En cas de bug, s'assurer qu'on revient sur la fenêtre principale
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
                continue

        # Pause entre les pages
        human_wait(4.0, 8.0)

    driver.quit()
    return pd.DataFrame(results)

# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    df = scrape_idealista_valencia(pages=1)  # adapte selon ce que tu veux
    df.to_csv("data/idealista_valencia.csv", index=False)
    print("Terminé. Données sauvegardées.")
