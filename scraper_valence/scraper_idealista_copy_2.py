import time
import random
from urllib.parse import urljoin
import re

import requests
import pandas as pd
from bs4 import BeautifulSoup

# -------------------------
# CONFIG HTTP FURTIF
# -------------------------

# Quelques user-agents pour tourner un peu
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

BASE_DOMAIN = "https://www.idealista.com"


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8,fr;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }


# -------------------------
# FETCH UTIL
# -------------------------

def fetch_url(url, session=None, sleep_range=(2, 5)):
    """
    Fetch une URL avec headers 'humains' + petite pause.
    """
    if session is None:
        session = requests.Session()

    headers = get_headers()

    resp = session.get(url, headers=headers, timeout=15)
    # Optionnel : gérer 403 / 429 ici si tu veux
    if resp.status_code != 200:
        print(f"[WARN] {resp.status_code} sur {url}")
        return None

    # Pause pseudo-humaine
    time.sleep(random.uniform(*sleep_range))
    return resp.text


# -------------------------
# PARSING LISTING (PAGE RESULTATS)
# -------------------------

def parse_listing_page(html, page_url):
    """
    Parse une page de résultats Idealista et retourne une liste de dicts
    avec les infos de base + URL de détail.
    """
    soup = BeautifulSoup(html, "html.parser")

    ads = soup.find_all("div", class_="item-info-container")
    listings = []

    for ad in ads:
        try:
            # Titre + lien
            link_tag = ad.find("a", class_="item-link")
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            rel_link = link_tag.get("href")
            link = urljoin(BASE_DOMAIN, rel_link)

            # Prix
            price_tag = ad.find("span", class_="item-price")
            if price_tag:
                price_text = price_tag.get_text(strip=True)
            else:
                price_text = ""

            # Nettoyage prix → int
            price_num = None
            if price_text:
                # garde seulement chiffres
                digits = re.sub(r"[^\d]", "", price_text)
                if digits:
                    price_num = int(digits)

            # Surface : dans item-detail ou item-detail-char
            surface = None
            # Plusieurs variantes selon la langue / layout
            detail_blocks = ad.find_all(
                ["span", "div"],
                class_=lambda c: c and ("item-detail" in c or "item-detail-char" in c),
            )
            for db in detail_blocks:
                txt = db.get_text(" ", strip=True)
                if "m²" in txt or "m2" in txt:
                    # extraire le premier nombre
                    m = re.search(r"(\d+(\.\d+)?)", txt.replace(",", "."))
                    if m:
                        surface = float(m.group(1))
                        break

            # Quartier / sous-titre
            barrio = ""
            subt = ad.select_one(".item-subtitle, .item-location")
            if subt:
                barrio = subt.get_text(strip=True)

            listings.append(
                {
                    "Titre du bien": title,
                    "Quartier": barrio,
                    "Surface (m²)": surface,
                    "Prix d’achat (€)": price_num,
                    "Lien annonce": link,
                }
            )
        except Exception as e:
            print("Erreur parsing listing de la page:", e)
            continue

    return listings


# -------------------------
# PARSING PAGE ANNONCE
# -------------------------

def parse_detail_page(html):
    """
    Parse le HTML d'une page d'annonce Idealista pour:
    - Description
    - Agence
    - Coordonnées (lat, lon)
    - Photos
    """
    soup = BeautifulSoup(html, "html.parser")

    # Description (plusieurs variantes possibles)
    description = ""
    for selector in [".comment", ".comment-text", ".adCommentsLanguage"]:
        tag = soup.select_one(selector)
        if tag:
            description = tag.get_text(" ", strip=True)
            break

    # Agence
    agency = ""
    agency_tag = soup.select_one(".about-agency-name, .about-agency-title")
    if agency_tag:
        agency = agency_tag.get_text(strip=True)

    # Coordonnées depuis les scripts
    coords = ""
    lat = lon = None
    for script in soup.find_all("script"):
        txt = script.string or script.get_text()
        if not txt:
            continue
        if "latitude" in txt and "longitude" in txt:
            # très rustique mais suffisant
            lat_match = re.search(r"latitude[\"']?\s*[:=]\s*([0-9\.\-]+)", txt)
            lon_match = re.search(r"longitude[\"']?\s*[:=]\s*([0-9\.\-]+)", txt)
            if lat_match and lon_match:
                lat = lat_match.group(1)
                lon = lon_match.group(1)
                coords = f"{lat}, {lon}"
                break

    # Photos
    photos = set()

    # 1) Images dans le carrousel principal
    for img in soup.select("#main-multimedia img, img.detail-image-gallery"):
        src = img.get("data-ondemand-img") or img.get("data-src") or img.get("src")
        if src and "px.png" not in src:
            photos.add(src)

    return {
        "Description": description,
        "Agence": agency,
        "Coordonnées": coords,
        "Photos": list(photos),
    }


# -------------------------
# SCRAPER GLOBAL
# -------------------------

def scrape_idealista_valencia(pages=5):
    """
    Scrape Idealista (Valence) sur X pages de résultats via HTTP.
    Retourne un DataFrame.
    """
    base_url = "https://www.idealista.com/en/venta-viviendas/valencia-valencia/pagina-"

    session = requests.Session()
    all_rows = []

    for p in range(1, pages + 1):
        url = f"{base_url}{p}.htm"
        print(f"Scraping listing page: {url}")

        html_list = fetch_url(url, session=session, sleep_range=(3, 6))
        if not html_list:
            print(f"[WARN] Impossible de récupérer la page {url}")
            continue

        listings = parse_listing_page(html_list, url)

        print(f"  -> {len(listings)} annonces trouvées sur la page {p}")

        # Pour chaque annonce, aller chercher les détails
        for ad in listings:
            ad_url = ad["Lien annonce"]
            print(f"    Détail: {ad_url}")

            detail_html = fetch_url(ad_url, session=session, sleep_range=(2, 5))
            if not detail_html:
                print(f"    [WARN] Impossible de récupérer l'annonce {ad_url}")
                continue

            detail_data = parse_detail_page(detail_html)

            row = {
                "Titre du bien": ad["Titre du bien"],
                "Quartier": ad["Quartier"],
                "Surface (m²)": ad["Surface (m²)"],
                "Prix d’achat (€)": ad["Prix d’achat (€)"],
                "Description": detail_data["Description"],
                "Lien annonce": ad["Lien annonce"],
                "Agence": detail_data["Agence"],
                "Coordonnées": detail_data["Coordonnées"],
                "Photos": detail_data["Photos"],
            }

            all_rows.append(row)

    df = pd.DataFrame(all_rows)
    return df


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    df = scrape_idealista_valencia(pages=5)
    df.to_csv("data/idealista_valencia_http.csv", index=False)
    print("Terminé. Données sauvegardées dans data/idealista_valencia_http.csv")

