import subprocess  # Pour exécuter des commandes système externes (ici mongodump)
import datetime    # Pour gérer les dates et générer des noms de fichiers uniques
import boto3       # Pour interagir avec AWS S3
import os          # Pour accéder aux variables d'environnement

MONGO_URI = os.getenv("MONGO_URI_AWS", "mongodb://16.171.43.201:27017") # Récupère l'URI MongoDB depuis une variable d'environnement, ou utilise une valeur par défaut
BUCKET = "p8-meteo" # Nom du bucket S3 où sera stocké le backup
BACKUP_PREFIX = "p8-backups/mongodb"  # Dossier dans le bucket pour organiser les backups

date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # On ajoute la date et l'heure pour que chaque backup ait un nom unique
backup_file = rf"C:\Users\zakar_2tvurct\Desktop\Formation Data Engineer\Projet 8\mongodb_backup_{date_str}.gz" # Ici, le backup sera un fichier compressé (.gz) sur disque local

print("Création du backup MongoDB...") # Affichage du message de début de la création du backup
subprocess.run([ # Exécute la commande mongodump pour créer le backup
    "mongodump", # Commande à exécuter pour exporter les données de MongoDB
    "--uri", MONGO_URI, # URI de connexion à MongoDB
    "--archive=" + backup_file, # Chemin du fichier de backup
    "--gzip" # Compression du backup en format gzip
], check=True) # Vérifie que la commande s'est exécutée avec succès
# check=True : si la commande échoue, Python lève une exception et arrête le script

s3 = boto3.client("s3") # Création du client S3 pour interagir avec AWS S3
s3_key = f"{BACKUP_PREFIX}/mongodb_backup_{date_str}.gz" # Clé S3 (chemin dans le bucket) pour le backup

print("Upload du backup vers S3...") # Affichage du message de début de l'upload du backup vers S3
s3.upload_file(backup_file, BUCKET, s3_key) # Upload du backup vers S3

print(f"Backup terminé : s3://{BUCKET}/{s3_key}") # Affichage du message de fin de l'upload du backup vers S3   
