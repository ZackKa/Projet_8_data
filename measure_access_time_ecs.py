import time  # Pour mesurer le temps d'exécution de certaines opérations
from pymongo import MongoClient  # Pour se connecter à MongoDB et interagir avec la base
import os  # Pour accéder aux variables d'environnement (utile pour les configurations)

# Configuration
# Récupère l'URI de connexion MongoDB depuis les variables d'environnement.
# Si la variable n'existe pas, on utilise l'URI par défaut fourni (ex. serveur AWS)
MONGO_URI_AWS = os.getenv("MONGO_URI_AWS", "mongodb://16.170.213.236:27017")

DB_NAME = "p8_greenandcoop_forecast" # Nom de la base de données à utiliser
COLLECTION_NAME = "weather_data" # Nom de la collection  où les données météo sont stockées

client = MongoClient(MONGO_URI_AWS) # Création du client MongoDB avec l'URI fourni
db = client[DB_NAME] # Sélection de la base de données à utiliser
collection = db[COLLECTION_NAME] # Sélection de la collection à utiliser

# Requête métier : station + journée
# On veut récupérer toutes les mesures pour une station précise sur une journée donnée
query = {
    "station.name": "WeerstationBS",
    "timestamp": {"$regex": "^2024-10-01"}
}
#"station.name": "WeerstationBS"
#"station.name": "La Madeleine"

start = time.perf_counter() # Commence le chronomètre avant la requête
results = list(collection.find(query)) # Exécution de la requête sur MongoDB et conversion des résultats en liste Python
end = time.perf_counter() # Arrête le chronomètre après la requête

print(f"Documents WeerstationBS du 01/10/2024 récupérés : {len(results)}") # Nombre de documents récupérés pour cette station à cette journée
print(f"Temps d'accès aux données WeerstationBS du 01/10/2024 : {end - start:.4f} secondes") # Temps d'exécution de la requête en secondes
