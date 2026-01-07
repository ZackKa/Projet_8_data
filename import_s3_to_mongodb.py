import json  # Pour lire et manipuler des fichiers JSON
import boto3  # Pour interagir avec Amazon S3
from pymongo import MongoClient  # Pour interagir avec MongoDB

# ----- CONFIGURATION -----
BUCKET = "p8-meteo"  # Nom du bucket S3
KEY = "p8-processed/weather_mongodb_ready.json"  # Chemin/fichier JSON dans le bucket

MONGO_URI = "mongodb://localhost:27017"  # URI de connexion à MongoDB local
DB_NAME = "p8_greenandcoop_forecast" # Nom de la base de données
COLLECTION_NAME = "weather_data" # Nom de la collection


# ----- CONNECTION -----
s3 = boto3.client("s3") # Création du client S3 pour accéder aux fichiers dans le cloud AWS S3
client = MongoClient(MONGO_URI) # Création du client MongoDB pour se connecter à la base locale
db = client[DB_NAME] # Sélection de la base de données
collection = db[COLLECTION_NAME] # Sélection de la collection où les documents seront insérés


# ----- LIRE LE FICHIER JSON DEPUIS S3 -----
print("Récupération du fichier depuis S3...")
obj = s3.get_object(Bucket=BUCKET, Key=KEY) # Récupération du fichier JSON depuis S3
data = json.load(obj["Body"]) # Lecture et parsing du JSON directement depuis le "Body" de la réponse
print(f"Nombre de documents à importer : {len(data)}") # Affichage du nombre de documents à importer


# ----- IMPORT DANS MONGODB -----
inserted_count = 0 # Initialisation du compteur pour suivre le nombre de documents importés
for doc in data: # Boucle pour parcourir chaque document du fichier JSON
    try:
        collection.insert_one(doc) # Insertion du document dans MongoDB
        inserted_count += 1 # Incrémentation du compteur pour suivre le nombre de documents importés
    except Exception as e: # e représente l’objet exception qui a été levé par Python
        print(f"Erreur à l’insertion : {e}") # Affichage de l'erreur si une erreur survient lors de l'insertion 
print(f"Documents importés avec succès : {inserted_count}") # Affichage du nombre de documents importés avec succès


# ----- CONTROLE QUALITE POST-IMPORT -----
print("\n--- Vérification post-import ---")
total_docs = collection.count_documents({}) # Récupération du nombre total de documents dans la collection
print(f"Total documents en base : {total_docs}")

# Doublons station_id + timestamp
# Pipeline d'aggregation pour détecter les doublons dans la collection en groupant par station_id et timestamp
pipeline = [
    {"$group": {"_id": {"station_id": "$station.station_id", "timestamp": "$timestamp"}, "count": {"$sum": 1}}}, # Groupe par station_id et timestamp et Compte combien de fois chaque combinaison apparaît
    {"$match": {"count": {"$gt": 1}}} # Filtre pour ne garder que les groupes avec plus d'un document
]
duplicates = list(collection.aggregate(pipeline)) # Exécution de l'aggregation et conversion en liste
print(f"Nombre de doublons détectés : {len(duplicates)}")

# Valeurs critiques manquantes
# Compte le nombre de documents où certaines mesures sont absentes
missing_temp = collection.count_documents({"measurements.temperature_c": None}) # Compte le nombre de documents sans température
missing_humidity = collection.count_documents({"measurements.humidity_pct": None}) # Compte le nombre de documents sans humidité
missing_pressure = collection.count_documents({"measurements.pressure_hpa": None}) # Compte le nombre de documents sans pression
print(f"Documents sans température : {missing_temp}") 
print(f"Documents sans humidité : {missing_humidity}")
print(f"Documents sans pression : {missing_pressure}")

print("\n--- Import terminé ---")
