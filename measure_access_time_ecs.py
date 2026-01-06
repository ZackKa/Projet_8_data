import time
from pymongo import MongoClient
import os

# Configuration
MONGO_URI_AWS = os.getenv("MONGO_URI_AWS", "mongodb://16.170.213.236:27017")

DB_NAME = "p8_greenandcoop_forecast"
COLLECTION_NAME = "weather_data"

client = MongoClient(MONGO_URI_AWS)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Requête métier : station + journée
query = {
    "station.name": "WeerstationBS",
    "timestamp": {"$regex": "^2024-10-01"}
}
#"station.name": "WeerstationBS"
#"station.name": "La Madeleine"

start = time.perf_counter()
results = list(collection.find(query))
end = time.perf_counter()

print(f"Documents WeerstationBS du 01/10/2024 récupérés : {len(results)}")
print(f"Temps d'accès aux données WeerstationBS du 01/10/2024 : {end - start:.4f} secondes")
