"""
Télécharge les données brutes nécessaires au projet (avec cache : un fichier déjà
présent n'est pas re-téléchargé).

  - Fichiers DVF « ValeursFoncieres-AAAA.txt » depuis data.gouv.fr -> data/raw/
  - Contours des départements (GeoJSON simplifié)                  -> data/

Usage :  python download_data.py                 (années par défaut : 2022 à 2026)
         python download_data.py 2023 2024       (années choisies)

Les fichiers peuvent aussi être téléchargés à la main sur
https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/
puis décompressés dans data/raw/.
"""
import io
import re
import sys
import zipfile
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
GEOJSON = Path("data/departements.geojson")
DATASET_API = "https://www.data.gouv.fr/api/1/datasets/demandes-de-valeurs-foncieres/"
GEOJSON_URL = ("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
               "departements-version-simplifiee.geojson")
DEFAULT_YEARS = ["2022", "2023", "2024", "2025", "2026"]


def download_geojson() -> None:
    if GEOJSON.exists():
        print(f"OK (déjà présent) : {GEOJSON}")
        return
    r = requests.get(GEOJSON_URL, timeout=60)
    r.raise_for_status()
    GEOJSON.write_bytes(r.content)
    print(f"Téléchargé : {GEOJSON}")


def dvf_resources() -> dict[str, str]:
    """{'2024': url, '2026-s1': url, ...} d'après l'API data.gouv.fr."""
    r = requests.get(DATASET_API, timeout=60)
    r.raise_for_status()
    found = {}
    for res in r.json().get("resources", []):
        url = res.get("url", "")
        m = re.search(r"valeursfoncieres-(\d{4}(?:-s\d)?)\.txt(?:\.zip)?$", url, re.I)
        if m:
            found[m.group(1).lower()] = url
    return found


def download_dvf(years: list[str]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    resources = dvf_resources()
    for key, url in sorted(resources.items()):
        if key[:4] not in years:
            continue
        if any(RAW_DIR.glob(f"ValeursFoncieres-{key[:4]}*.txt")):
            print(f"OK (déjà présent) : {key}")
            continue
        print(f"Téléchargement {key} ({url}) ...")
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        if url.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                z.extractall(RAW_DIR)
        else:
            (RAW_DIR / Path(url).name).write_bytes(r.content)
    print(f"Fichiers bruts dans {RAW_DIR}/ :", sorted(p.name for p in RAW_DIR.glob("*.txt")))


if __name__ == "__main__":
    download_geojson()
    download_dvf(sys.argv[1:] or DEFAULT_YEARS)
    print("Étape suivante : python prepare_data.py")
