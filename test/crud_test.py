from pymongo import MongoClient
from datetime import datetime
import pprint

# -----------------------
# Configuration MongoDB
# -----------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "p8_greenandcoop_forecast"
COLLECTION_NAME = "weather_data"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

pp = pprint.PrettyPrinter(indent=2)

print("Connexion à MongoDB réussie")

# -----------------------
# CREATE
# -----------------------
test_document = {
    "source": "crud_test",
    "timestamp": datetime.utcnow().isoformat(),
    "measurements": {
        "humidity_pct": 55.0,
        "pressure_hpa": 1013.2,
        "temperature_c": 18.5,
        "wind_speed_kmh": 12.3,
        "wind_gust_kmh": 20.1,
        "clouds_octas": None,
        "precip_1h_mm": 0,
        "precip_3h_mm": 0,
        "snow_cm": 0,
        "visibility_m": None,
        "weather_code": None,
        "wind_direction_deg": None
    },
    "station": {
        "name": "Station Test CRUD",
        "station_id": "TEST_CRUD_001",
        "city": "TestCity",
        "country": "FR",
        "elevation": 100,
        "latitude": 48.8566,
        "longitude": 2.3522,
        "type": "test",
        "source": "internal",
        "software": "python",
        "hardware": "virtual",
        "license": {
            "license": "test",
            "metadonnees": "test",
            "source": "test",
            "url": "https://example.com"
        },
        "location": {
            "elevation": 100,
            "lat": 48.8566,
            "lon": 2.3522
        }
    }
}

result = collection.insert_one(test_document)
test_id = result.inserted_id

print("\n[CREATE] Document inséré avec _id :")
print(test_id)

# -----------------------
# READ
# -----------------------
print("\n[READ] Document inséré :")
document = collection.find_one({"_id": test_id})
pp.pprint(document)

# -----------------------
# UPDATE
# -----------------------
update_result = collection.update_one(
    {"_id": test_id},
    {"$set": {"measurements.temperature_c": 19.0}}
)

print(f"\n[UPDATE] Documents modifiés : {update_result.modified_count}")

updated_document = collection.find_one({"_id": test_id})
print("\n[READ AFTER UPDATE] Document mis à jour :")
pp.pprint(updated_document)

# -----------------------
# DELETE
# -----------------------
delete_result = collection.delete_one({"_id": test_id})
print(f"\n[DELETE] Documents supprimés : {delete_result.deleted_count}")

# -----------------------
# Vérification finale
# -----------------------
final_check = collection.find_one({"_id": test_id})
print("\n[VÉRIFICATION] Document encore présent ?")
print(final_check)

client.close()
print("\nTest CRUD terminé avec succès.")
