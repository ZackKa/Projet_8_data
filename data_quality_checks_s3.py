import boto3
import json

BUCKET = "p8-meteo"
KEY = "p8-processed/weather_mongodb_ready.json"

s3 = boto3.client("s3")

obj = s3.get_object(Bucket=BUCKET, Key=KEY)
data = json.loads(obj["Body"].read())

total = len(data)
missing = 0
duplicates = set()
duplicate_count = 0

for d in data:
    if d["measurements"]["temperature_c"] is None:
        missing += 1

    key = (d["station"].get("station_id"), d["timestamp"])
    if key in duplicates:
        duplicate_count += 1
    else:
        duplicates.add(key)

error_rate = ((missing + duplicate_count) / total) * 100 if total else 0

report = {
    "total_records": total,
    "missing_temperature": missing,
    "duplicate_records": duplicate_count,
    "error_rate_percent": round(error_rate, 2)
}

s3.put_object(
    Bucket=BUCKET,
    Key="p8-processed/quality_report.json",
    Body=json.dumps(report, indent=2).encode("utf-8")
)

print("📊 Rapport qualité écrit dans S3")
print(report)
