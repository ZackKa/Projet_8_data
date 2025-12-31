import boto3
import json
from datetime import datetime, timedelta
import re

BUCKET = "p8-meteo"

RAW_PREFIXES = {
    "france": "p8-data-path/France_data/",
    "belgique": "p8-data-path/Belgique_data/",
    "infoclimat": "p8-data-path/InfoClimat_data/"
}

OUTPUT_KEY = "p8-processed/weather_mongodb_ready.json"

s3 = boto3.client("s3")

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

# ---------- utils conversions ----------
def extract_number(value):
    return float(re.findall(r"[-+]?\d*\.\d+|\d+", value)[0])

def f_to_c(f): return round((f - 32) * 5/9, 2)
def mph_to_kmh(v): return round(v * 1.60934, 2)
def inhg_to_hpa(v): return round(v * 33.8639, 2)

# ---------- S3 helpers ----------
def list_objects(prefix):
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    return [o["Key"] for o in resp.get("Contents", [])]

# ---------- Weather Underground ----------
def process_weather_underground(prefix, station_key, start_date):
    docs = []
    keys = list_objects(prefix)

    current_date = start_date
    previous_time = None

    for key in keys:
        obj = s3.get_object(Bucket=BUCKET, Key=key)

        for line in obj["Body"].iter_lines():
            record = json.loads(line)
            data = record["_airbyte_data"]

            time_str = data["Time"]  # HH:MM:SS
            current_time = datetime.strptime(time_str, "%H:%M:%S").time()

            if previous_time and current_time < previous_time:
                current_date += timedelta(days=1)

            previous_time = current_time

            timestamp = datetime.combine(current_date, current_time).isoformat() + "Z"

            doc = {
                "source": "weather_underground",
                "station": STATIONS[station_key],
                "timestamp": timestamp,
                "measurements": {
                    "temperature_c": f_to_c(extract_number(data["Temperature"])),
                    "humidity_pct": extract_number(data["Humidity"]),
                    "pressure_hpa": inhg_to_hpa(extract_number(data["Pressure"])),
                    "wind_speed_kmh": mph_to_kmh(extract_number(data["Speed"])),
                    "wind_gust_kmh": mph_to_kmh(
                        extract_number(data.get("Gust", "0"))
                    )
                }
            }
            docs.append(doc)

    return docs

# ---------- InfoClimat ----------
def process_infoclimat(prefix):
    docs = []
    keys = list_objects(prefix)

    for key in keys:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        for line in obj["Body"].iter_lines():
            record = json.loads(line)
            data = record["_airbyte_data"]

            # Construire un dictionnaire des stations avec métadonnées complètes
            stations_meta = {}
            for s in data.get("stations", []):
                stations_meta[s["id"]] = {
                    "station_id": s["id"],
                    "name": s["name"],
                    "latitude": s.get("latitude"),
                    "longitude": s.get("longitude"),
                    "elevation": s.get("elevation"),
                    "type": s.get("type"),
                    "license": s.get("license", {})
                }

            hourly = data.get("hourly", {})
            for station_id, measures in hourly.items():
                for m in measures:
                    # Vérifie si m est une chaîne et essaie de la convertir en dict
                    if isinstance(m, str) and m.strip() != "":
                        try:
                            m = json.loads(m)
                        except json.JSONDecodeError:
                            continue  # ignore les lignes invalides

                    # Création d'un document standardisé
                    doc = {
                        "source": "infoclimat",
                        "station": stations_meta.get(station_id, {"station_id": station_id}),
                        "timestamp": m.get("dh_utc", None) + "Z" if m.get("dh_utc") else None,
                        "measurements": {
                            "temperature_c": float(m["temperature"]) if m.get("temperature") else None,
                            "humidity_pct": float(m["humidite"]) if m.get("humidite") else None,
                            "pressure_hpa": float(m["pression"]) if m.get("pression") else None,
                            "wind_speed_kmh": float(m["vent_moyen"]) if m.get("vent_moyen") else None,
                            "wind_gust_kmh": float(m["vent_rafales"]) if m.get("vent_rafales") else None,
                            "wind_direction_deg": float(m["vent_direction"]) if m.get("vent_direction") else None,
                            "precip_1h_mm": float(m["pluie_1h"]) if m.get("pluie_1h") else 0,
                            "precip_3h_mm": float(m["pluie_3h"]) if m.get("pluie_3h") else 0,
                            "snow_cm": float(m["neige_au_sol"]) if m.get("neige_au_sol") else 0,
                            "visibility_m": float(m["visibilite"]) if m.get("visibilite") else None,
                            "clouds_octas": float(m["nebulosite"]) if m.get("nebulosite") else None,
                            "weather_code": m.get("temps_omm")
                        }
                    }
                    docs.append(doc)
    return docs


def main():
    all_docs = []

    all_docs += process_weather_underground(
        RAW_PREFIXES["france"], "france",
        start_date=datetime(2024, 10, 1).date()
    )

    all_docs += process_weather_underground(
        RAW_PREFIXES["belgique"], "belgique",
        start_date=datetime(2024, 10, 1).date()
    )

    all_docs += process_infoclimat(RAW_PREFIXES["infoclimat"])

    s3.put_object(
        Bucket=BUCKET,
        Key=OUTPUT_KEY,
        Body=json.dumps(all_docs, indent=2).encode("utf-8")
    )

    print(f"✅ {len(all_docs)} documents écrits dans s3://{BUCKET}/{OUTPUT_KEY}")

if __name__ == "__main__":
    main()
