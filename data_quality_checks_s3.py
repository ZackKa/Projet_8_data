import boto3  # Pour interagir avec AWS S3
import json   # Pour manipuler des fichiers JSON

BUCKET = "p8-meteo" # Nom du bucket S3 où sont stockées les données
KEY = "p8-processed/weather_mongodb_ready.json"  # Fichier JSON à analyser

s3 = boto3.client("s3") # crée un “client” pour S3, c’est-à-dire un objet Python qui sait parler au service S3

obj = s3.get_object(Bucket=BUCKET, Key=KEY) # Récupération du fichier JSON depuis S3
data = json.loads(obj["Body"].read()) # Lecture et parsing du JSON directement depuis le "Body" de la réponse. convertion en liste de dictionnaires Python

# ---------- Initialisation des compteurs ----------
total = len(data) # Nombre total de documents dans le fichier JSON
missing = 0 # Nombre de documents sans température
duplicates = set() # Ensemble pour stocker les doublons (station_id + timestamp)
duplicate_count = 0 # Nombre de doublons détectés

# ---------- Parcours de chaque enregistrement ----------
for d in data: # Parcourt chaque document dans la liste
    if d["measurements"]["temperature_c"] is None:  # Vérifie si la température est manquante (None)
        missing += 1

    key = (d["station"].get("station_id"), d["timestamp"]) # Création d'une clé unique basée sur l'ID de la station et le timestamp
    if key in duplicates: # Vérifie si la clé existe déjà dans l'ensemble des doublons
        duplicate_count += 1 # Incrémentation du compteur de doublons
    else:
        duplicates.add(key) # Ajout de la clé à l'ensemble des doublons si elle n'existe pas déjà

# ---------- Calcul du taux d'erreur ----------
# On additionne les mesures manquantes et les doublons, puis on divise par le total
error_rate = ((missing + duplicate_count) / total) * 100 if total else 0 # Calcul du taux d'erreur en pourcentage
# Si total > 0 (il y a des enregistrements) → on calcule le taux d’erreur normalement.
# Si total == 0 (le fichier est vide) → on met le taux d’erreur à 0 pour éviter une division par zéro.

# ---------- Création du rapport qualité ----------
report = {
    "total_records": total, # Nombre total d'enregistrements
    "missing_temperature": missing, # Nombre de documents sans température
    "duplicate_records": duplicate_count, # Nombre de doublons
    "error_rate_percent": round(error_rate, 2) # Taux d'erreur en pourcentage
}

s3.put_object( # Écrit le rapport qualité dans S3
    Bucket=BUCKET, # Nom du bucket S3
    Key="p8-processed/quality_report.json", # Nouveau fichier JSON pour le rapport
    Body=json.dumps(report, indent=2).encode("utf-8") # Conversion du rapport en JSON et encodage en UTF-8
)

print("📊 Rapport qualité écrit dans S3") # Affichage du rapport qualité
print(report) # Affichage du rapport qualité
