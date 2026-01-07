from pymongo import MongoClient  # Pour se connecter et interagir avec MongoDB
from datetime import datetime, timezone  # Pour manipuler les dates/horodatages en UTC
import pprint  # Pour afficher de façon lisible les documents JSON

# -----------------------
# Configuration MongoDB
# -----------------------
MONGO_URI = "mongodb://localhost:27017"  # URI de connexion à MongoDB local
DB_NAME = "p8_greenandcoop_forecast"     # Nom de la base de données
COLLECTION_NAME = "weather_data_crud_test"  # Nom de la collection de test

client = MongoClient(MONGO_URI) # Création du client MongoDB
db = client[DB_NAME] # Sélection de la base de données
collection = db[COLLECTION_NAME] # Sélection de la collection

pp = pprint.PrettyPrinter(indent=2) # Initialisation du pretty printer pour afficher les documents de façon lisible

print("Connexion à MongoDB réussie (collection de test)")

# -----------------------
# CREATE
# -----------------------
# Création d'un document test avec des mesures météo fictives et infos sur la station
test_document = {
    "source": "crud_test",
    "timestamp": datetime.now(timezone.utc).isoformat(),  # datetime aware UTC. # Horodatage UTC ISO 8601 pour garder une trace du moment de l'enregistrement
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
        "station_id": "TEST_CRUD_002",
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

result = collection.insert_one(test_document) # Insertion du document dans MongoDB
test_id = result.inserted_id # Récupération de l'ID du document inséré

print("\n[CREATE] Document inséré avec _id :")
print(test_id)

# -----------------------
# READ
# -----------------------
print("\n[READ] Document inséré :")
document = collection.find_one({"_id": test_id}) # Recherche du document par son ID
pp.pprint(document) # Affichage du document de façon lisible

# -----------------------
# UPDATE
# -----------------------
update_result = collection.update_one( # Mise à jour du document
    {"_id": test_id}, # Filtre pour cibler le document
    {"$set": {"measurements.temperature_c": 19.0}}
) # Mise à jour de la température en 19.0°C

print(f"\n[UPDATE] Documents modifiés : {update_result.modified_count}")

updated_document = collection.find_one({"_id": test_id}) # Recherche du document par son ID
print("\n[READ AFTER UPDATE] Document mis à jour :")
pp.pprint(updated_document) # Affichage du document de façon lisible

# -----------------------
# DELETE
# -----------------------
delete_result = collection.delete_one({"_id": test_id}) # Suppression du document par son ID
print(f"\n[DELETE] Documents supprimés : {delete_result.deleted_count}")

# -----------------------
# Vérification finale
# -----------------------
final_check = collection.find_one({"_id": test_id}) # Recherche du document par son ID
print("\n[VÉRIFICATION] Document encore présent ?")
print(final_check) # Affichage du document de façon lisible après la suppression

client.close() # Fermeture de la connexion MongoDB  
print("\nTest CRUD terminé avec succès (nouvelle collection).")
