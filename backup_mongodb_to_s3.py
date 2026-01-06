import subprocess
import datetime
import boto3
import os

MONGO_URI = os.getenv("MONGO_URI_AWS", "mongodb://16.170.213.236:27017")
BUCKET = "p8-meteo"
BACKUP_PREFIX = "p8-backups/mongodb"

date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = rf"C:\Users\zakar_2tvurct\Desktop\Formation Data Engineer\Projet 8\mongodb_backup_{date_str}.gz"

print("Création du backup MongoDB...")
subprocess.run([
    "mongodump",
    "--uri", MONGO_URI,
    "--archive=" + backup_file,
    "--gzip"
], check=True)

s3 = boto3.client("s3")
s3_key = f"{BACKUP_PREFIX}/mongodb_backup_{date_str}.gz"

print("Upload du backup vers S3...")
s3.upload_file(backup_file, BUCKET, s3_key)

print(f"Backup terminé : s3://{BUCKET}/{s3_key}")
