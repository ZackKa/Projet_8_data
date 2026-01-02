FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY import_s3_to_mongodb_conteneur.py .

CMD ["python", "import_s3_to_mongodb_conteneur.py"]
