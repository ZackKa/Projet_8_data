import boto3           # Pour interagir avec Amazon S3
import json            # Pour manipuler des fichiers JSON
from datetime import datetime, timedelta  # Pour gérer dates et heures
import re              # Pour les expressions régulières (extraction de nombres)

BUCKET = "p8-meteo"# Nom du bucket S3 où sont stockées les données

RAW_PREFIXES = {
    "france": "p8-data-path/France_data/",
    "belgique": "p8-data-path/Belgique_data/",
    "infoclimat": "p8-data-path/InfoClimat_data/"
} # Préfixes pour chaque source de données brute dans le bucket

OUTPUT_KEY = "p8-processed/weather_mongodb_ready.json" # Chemin du fichier JSON final traité qui sera écrit dans S3

s3 = boto3.client("s3") # Création du client S3 pour récupérer et écrire des fichiers dans le cloud AWS S3 

# Métadonnées stations amateurs
STATIONS = {
    "france": {
        "station_id": "ILAMAD25",
        "name": "La Madeleine",
        "city": "La Madeleine",
        "country": "FR",
        "location": {
            "lat": 50.659,
            "lon": 3.07,
            "elevation": 23
        },
        "hardware": "other",
        "software": "EasyWeatherPro_V5.1.6",
        "source": "weather_underground"
    },
    "belgique": {
        "station_id": "IICHTE19",
        "name": "WeerstationBS",
        "city": "Ichtegem",
        "country": "BE",
        "location": {
            "lat": 51.092,
            "lon": 2.999,
            "elevation": 15
        },
        "hardware": "other",
        "software": "EasyWeatherV1.6.6",
        "source": "weather_underground"
    }
}

# ---------- FONCTIONS UTILITAIRES POUR CONVERSIONS ----------
# ---------- utils conversions ----------
def extract_number(value): #Extrait un nombre depuis une chaîne, même si la chaîne contient du texte.Par exemple: "23.5 C" -> 23.5
    return float(re.findall(r"[-+]?\d*\.\d+|\d+", value)[0]) #re.findall(r"[-+]?\d*\.\d+|\d+", value) est une expression régulière qui trouve tous les nombres (positifs ou négatifs) dans la chaîne value.

def f_to_c(f): return round((f - 32) * 5/9, 2) # Conversion de Fahrenheit en Celsius, arrondi à 2 décimales
def mph_to_kmh(v): return round(v * 1.60934, 2) # Conversion de Miles par heure en Kilomètres par heure, arrondi à 2 décimales
def inhg_to_hpa(v): return round(v * 33.8639, 2) # Conversion de Inch of mercury en Hectopascal, arrondi à 2 décimales

# ---------- S3 helpers ----------
# La fonction cherche tous les fichiers S3 sous un certain "dossier" (prefix) (par exemple "p8-data-path/France_data/" appeler dans main()) 
# et renvoie juste leurs noms complets pour que d’autres fonctions puissent les télécharger ou les traiter.
def list_objects(prefix): #Liste tous les objets (fichiers) dans un préfixe donné dans le bucket S3
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix) # Récupère la liste des objets dans le bucket S3
    return [o["Key"] for o in resp.get("Contents", [])] # Retourne la liste des clés des objets dans le bucket S3

# ---------- Weather Underground ----------
def process_weather_underground(prefix, station_key, start_date):
    # Traite les fichiers Weather Underground dans S3 pour un pays donné.
    #- prefix: chemin des fichiers bruts S3
    #- station_key: clé dans STATIONS (france ou belgique)
    #- start_date: date à laquelle commence les relevés
    # Retourne une liste de documents standardisés prêts pour MongoDB

    docs = [] # Liste finale des documents
    keys = list_objects(prefix)  # Liste des fichiers à traiter

    current_date = start_date  # Date de référence initiale
    previous_time = None  # Pour gérer les changements de jour entre 23:59 -> 00:00

    for key in keys:
        obj = s3.get_object(Bucket=BUCKET, Key=key) # Récupère le fichier depuis S3

        for line in obj["Body"].iter_lines(): # Parcourt chaque ligne du fichier (JSON par ligne)
            record = json.loads(line)  # Parse JSON
            data = record["_airbyte_data"] # Récupère les données du fichier à l'intérieur du format Airbyte

            time_str = data["Time"]  #  Heure du relevé au format HH:MM:SS
            current_time = datetime.strptime(time_str, "%H:%M:%S").time() # Convertit en objet time

            if previous_time and current_time < previous_time: # Si l'heure actuelle est inférieure à l'heure précédente, c'est un nouveau jour
                current_date += timedelta(days=1)

            previous_time = current_time

            timestamp = datetime.combine(current_date, current_time).isoformat() + "Z" # Création du timestamp ISO8601 pour MongoDB

            doc = { # Construction du document standardisé
                "source": "weather_underground",
                "station": STATIONS[station_key], # Récupère les métadonnées de la station
                "timestamp": timestamp, # Timestamp ISO8601
                "measurements": { # Mesures standardisées
                    "temperature_c": f_to_c(extract_number(data["Temperature"])),
                    "humidity_pct": extract_number(data["Humidity"]),
                    "pressure_hpa": inhg_to_hpa(extract_number(data["Pressure"])),
                    "wind_speed_kmh": mph_to_kmh(extract_number(data["Speed"])),
                    "wind_gust_kmh": mph_to_kmh(
                        extract_number(data.get("Gust", "0"))
                    )
                }
            }
            docs.append(doc) # Ajoute le document à la liste finale

    return docs # Retourne la liste des documents standardisés

# ---------- Description de la fonction process_weather_underground ----------

# Liste les fichiers S3 sous le préfixe donné (keys = list_objects(prefix))
# Initialise la date de départ (current_date) et l’heure précédente (previous_time)
# Parcourt chaque fichier et chaque ligne JSON :
    # Lit les données brutes (data = record["_airbyte_data"])
    # Récupère l’heure du relevé et ajuste la date si on passe minuit
    # Crée un timestamp ISO pour MongoDB
    # Transforme les mesures :
        # Température F → °C
        # Vitesse du vent mph → km/h
        # Pression inHg → hPa
    # Stocke tout dans un document standardisé avec station et source
# Retourne tous les documents pour ce pays/station

# ---------- Description de la fonction process_weather_underground ----------

# ---------- InfoClimat ----------
def process_infoclimat(prefix):
    # Traite les fichiers InfoClimat dans S3.
    #- prefix: chemin des fichiers bruts S3
    # Retourne une liste de documents standardisés pour MongoDB.

    docs = [] # Liste finale des documents
    keys = list_objects(prefix) # Liste des fichiers à traiter

    for key in keys: # Parcourt chaque fichier à traiter
        obj = s3.get_object(Bucket=BUCKET, Key=key) # Récupère le fichier depuis S3
        for line in obj["Body"].iter_lines(): # Parcourt chaque ligne du fichier (JSON par ligne)
            record = json.loads(line) # Parse JSON
            data = record["_airbyte_data"] # Récupère les données du fichier à l'intérieur du format Airbyte

            # Construire un dictionnaire des stations avec métadonnées complètes
            stations_meta = {} # Dictionnaire pour stocker les métadonnées des stations
            for s in data.get("stations", []): # Parcourt chaque station dans les données
                stations_meta[s["id"]] = { # Ajoute les métadonnées de la station au dictionnaire
                    "station_id": s["id"], # ID de la station
                    "name": s["name"], # Nom de la station
                    "latitude": s.get("latitude"), # Latitude de la station
                    "longitude": s.get("longitude"), # Longitude de la station
                    "elevation": s.get("elevation"), # Altitude de la station
                    "type": s.get("type"), # Type de la station
                    "license": s.get("license", {}) # Licence de la station
                }

            hourly = data.get("hourly", {}) # Récupère les données horaires des stations
            for station_id, measures in hourly.items(): # Parcourt chaque station et ses mesures horaires
                for m in measures: # Parcourt chaque mesure horaire
                    # Vérifie si m est une chaîne et essaie de la convertir en dict
                    if isinstance(m, str) and m.strip() != "": # Si m est une chaîne et n'est pas vide
                        try:
                            m = json.loads(m) # Convertit la chaîne en dictionnaire
                        except json.JSONDecodeError:
                            continue  # ignore les lignes invalides (si la conversion en dictionnaire échoue)

                    # Création d'un document standardisé
                    doc = {
                        "source": "infoclimat",
                        "station": stations_meta.get(station_id, {"station_id": station_id}), # Récupère les métadonnées de la station
                        "timestamp": m.get("dh_utc", None) + "Z" if m.get("dh_utc") else None, # Création du timestamp ISO8601 pour MongoDB
                        "measurements": {
                            "temperature_c": float(m["temperature"]) if m.get("temperature") else None, # Température en Celsius
                            "humidity_pct": float(m["humidite"]) if m.get("humidite") else None, # Humidité en pourcentage
                            "pressure_hpa": float(m["pression"]) if m.get("pression") else None, # Pression en Hectopascal
                            "wind_speed_kmh": float(m["vent_moyen"]) if m.get("vent_moyen") else None, # Vitesse moyenne du vent en Kilomètres par heure
                            "wind_gust_kmh": float(m["vent_rafales"]) if m.get("vent_rafales") else None, # Vitesse du vent en Kilomètres par heure
                            "wind_direction_deg": float(m["vent_direction"]) if m.get("vent_direction") else None, # Direction du vent en degrés
                            "precip_1h_mm": float(m["pluie_1h"]) if m.get("pluie_1h") else 0, # Pluie en Millimètres sur 1 heure
                            "precip_3h_mm": float(m["pluie_3h"]) if m.get("pluie_3h") else 0, # Pluie en Millimètres sur 3 heures
                            "snow_cm": float(m["neige_au_sol"]) if m.get("neige_au_sol") else 0, # Neige en Centimètres
                            "visibility_m": float(m["visibilite"]) if m.get("visibilite") else None, # Visibilité en Mètres
                            "clouds_octas": float(m["nebulosite"]) if m.get("nebulosite") else None, # Couverture nuageuse en Octas
                            "weather_code": m.get("temps_omm") # Code météo
                        }
                    }
                    docs.append(doc)
    return docs

# ---------- Description de la fonction process_infoclimat ----------

# Liste les fichiers S3 sous le préfixe InfoClimat

# Pour chaque fichier et chaque ligne JSON :
    # Crée un dictionnaire des stations avec métadonnées
    # Parcourt les relevés horaires de chaque station
    # Si la mesure est une chaîne JSON, la convertit en dictionnaire
    # Crée un document standardisé avec toutes les mesures possibles :
        # Température, humidité, pression, vent, précipitations, neige, visibilité, nébulosité, code météo
# Retourne tous les documents InfoClimat

# ---------- Description de la fonction process_infoclimat ----------

# ---------- Fonction principale ----------

def main():
    all_docs = [] # Liste finale des documents

    # Traiter les fichiers France Weather Underground depuis le 1er octobre 2024
    all_docs += process_weather_underground(
        RAW_PREFIXES["france"], "france", # Chemin des fichiers bruts S3 et clé dans STATIONS (france). station_key 1er element dans STATIONS sois france soit belgique
        start_date=datetime(2024, 10, 1).date() # Date de début des relevés
    )

    all_docs += process_weather_underground(
        RAW_PREFIXES["belgique"], "belgique", # Chemin des fichiers bruts S3 et clé dans STATIONS (belgique) station_key
        start_date=datetime(2024, 10, 1).date() # Date de début des relevés
    )

    all_docs += process_infoclimat(RAW_PREFIXES["infoclimat"]) # Traiter les fichiers InfoClimat

    # Écrire le résultat final dans S3 en JSON formaté
    s3.put_object(
        Bucket=BUCKET, # Nom du bucket S3
        Key=OUTPUT_KEY, # Chemin du fichier JSON final traité qui sera écrit dans S3
        Body=json.dumps(all_docs, indent=2).encode("utf-8") # Convertit la liste des documents en JSON formaté et l'encode en UTF-8
    )

    print(f"✅ {len(all_docs)} documents écrits dans s3://{BUCKET}/{OUTPUT_KEY}")

    # ---------- Description de la fonction main ----------

    # Initialise une liste vide all_docs
    # Appelle process_weather_underground pour la France et la Belgique → ajoute tous les documents à all_docs
    # Appelle process_infoclimat → ajoute tous les documents à all_docs
    # Écrit le fichier final JSON dans S3 (s3.put_object)

    # ---------- Description de la fonction main ----------

if __name__ == "__main__": 
    main() # Appelle la fonction principale
