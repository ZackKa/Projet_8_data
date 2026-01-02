import json
import boto3
from pymongo import MongoClient
import os

# ----- CONFIGURATION -----
BUCKET = "p8-meteo"
KEY = "p8-processed/weather_mongodb_ready.json"


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "p8_greenandcoop_forecast"
COLLECTION_NAME = "weather_data"


# ----- CONNECTION -----
s3 = boto3.client("s3")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ----- LIRE LE FICHIER JSON DEPUIS S3 -----
print("Récupération du fichier depuis S3...")
obj = s3.get_object(Bucket=BUCKET, Key=KEY)
data = json.load(obj["Body"])
print(f"Nombre de documents à importer : {len(data)}")

# ----- IMPORT DANS MONGODB -----
inserted_count = 0
for doc in data:
    try:
        collection.insert_one(doc)
        inserted_count += 1
    except Exception as e:
        print(f"Erreur à l’insertion : {e}")

print(f"Documents importés avec succès : {inserted_count}")

# ----- CONTROLE QUALITE POST-IMPORT -----
print("\n--- Vérification post-import ---")
total_docs = collection.count_documents({})
print(f"Total documents en base : {total_docs}")

# Doublons station_id + timestamp
pipeline = [
    {"$group": {"_id": {"station_id": "$station.station_id", "timestamp": "$timestamp"}, "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}}
]
duplicates = list(collection.aggregate(pipeline))
print(f"Nombre de doublons détectés : {len(duplicates)}")

# Valeurs critiques manquantes
missing_temp = collection.count_documents({"measurements.temperature_c": None})
missing_humidity = collection.count_documents({"measurements.humidity_pct": None})
missing_pressure = collection.count_documents({"measurements.pressure_hpa": None})
print(f"Documents sans température : {missing_temp}")
print(f"Documents sans humidité : {missing_humidity}")
print(f"Documents sans pression : {missing_pressure}")

print("\n--- Import terminé ---")
