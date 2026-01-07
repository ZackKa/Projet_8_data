FROM python:3.13-slim
# Utilise une image Docker légère (slim) contenant Python 3.13
# C'est la base du conteneur, elle contient juste Python et peu de dépendances système pour réduire la taille

WORKDIR /app
# Définit le répertoire de travail à l'intérieur du conteneur
# Toutes les commandes suivantes (COPY, RUN, CMD...) seront exécutées depuis /app

COPY requirements.txt .
# Copie le fichier requirements.txt du projet local vers le conteneur (/app/requirements.txt)

RUN pip install --no-cache-dir -r requirements.txt
# Installe toutes les dépendances Python listées dans requirements.txt
# --no-cache-dir évite de stocker les fichiers temporaires de pip pour garder l'image légère

COPY import_s3_to_mongodb_conteneur.py .
# Copie le script Python principal dans le conteneur
# Il sera donc accessible comme /app/import_s3_to_mongodb_conteneur.py à l'intérieur du conteneur

CMD ["python", "import_s3_to_mongodb_conteneur.py"]
# Définit la commande qui sera exécutée quand on lance le conteneur
# Ici, on lance directement le script Python qui importe les données S3 vers MongoDB