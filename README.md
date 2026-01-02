# README — Étape 1
Intégration et transformation de données météorologiques (Forecast 2.0)
Projet : GreenAndCoop – Forecast 2.0

Rôle : Data Engineer
Objectif de l’étape 1 :
Mettre en place un premier pipeline permettant de collecter, transformer, tester et stocker des données météorologiques issues de différentes sources dans Amazon S3, dans un format compatible avec une future intégration dans MongoDB.

## 1. Contexte du projet

Dans le cadre du projet Forecast 2.0, l’entreprise GreenAndCoop souhaite enrichir ses modèles de prévision de la demande électrique avec de nouvelles sources de données météorologiques, notamment :

Des stations semi-professionnelles du réseau InfoClimat

Des stations amateurs du réseau Weather Underground (France et Belgique)

Ces sources présentent :

des formats hétérogènes (JSON, Excel)

des fréquences différentes

des métadonnées variables

Le rôle du Data Engineer est de construire un pipeline fiable permettant de fournir des données propres, cohérentes et exploitables par les Data Scientists.

## 2. Architecture de l’étape 1

Vue d’ensemble

```java
Sources météo
   │
   ▼
Airbyte
   │
   ▼
Amazon S3 (zone RAW)
   │
   ▼
Scripts Python (transformation + tests)
   │
   ▼
Amazon S3 (zone PROCESSED, format MongoDB-ready)
```
Structure S3 utilisée

```pgsql
s3://p8-meteo/
│
├── p8-data-path/                # Données brutes (Airbyte)
│   ├── InfoClimat_data/
│   ├── France_data/
│   └── Belgique_data/
│
└── p8-processed/                # Données transformées
    ├── weather_mongodb_ready.json
    └── quality_report.json
```


## 3. Collecte des données (Airbyte)

La collecte est réalisée avec Airbyte, qui permet de :

se connecter aux différentes sources météo

uniformiser l’extraction

stocker les données brutes dans Amazon S3

Les données sont exportées au format JSONL dans un bucket S3.

👉 Aucune transformation n’est faite dans Airbyte
Toute la logique métier est volontairement gérée côté Python.


### 3.1 Installation et configuration d’Airbyte

Prérequis :

Docker Desktop installé et en fonctionnement

Terminal (PowerShell, CMD ou bash)

Installation Airbyte via Docker

Suivre les étapes de la documentation officiel:
https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart

Accéder à Airbyte :
Ouvrir un navigateur → http://localhost:8000


### 3.2 Préparation AWS

#### 3.2.1 Création d’un bucket S3

Connectez-vous à votre console AWS.

Allez dans S3 → Create bucket

Donnez un nom unique, ex : p8-meteo

Configurez la région (ex : eu-west-3)

Laissez les autres paramètres par défaut → Create bucket


#### 3.2.2 Création d’un utilisateur IAM pour Airbyte

Aller dans IAM → Users → Add user

Nom : airbyte-s3-user

Accès programmatique → cochez Programmatic access

Attachez la policy AmazonS3FullAccess

Cliquez sur Create user

Récupérez :

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

⚠️ Important : Conservez-les précieusement, ne les mettez pas dans Git.


### 3.3 Connexion Airbyte → AWS S3 (Destination)

Dans Airbyte :

Ajouter une destination

Type : Amazon S3

Renseignez :

Access Key ID → AWS_ACCESS_KEY_ID

Secret Access Key → AWS_SECRET_ACCESS_KEY

Bucket Name → p8-meteo

Region → eu-west-3

Testez la connexion → Save


### 3.4 Configuration Airbyte

Définition des sources et de la destination dans Airbyte

#### 3.4.1 Définir les sources météo

Dans Airbyte :

Ajouter une source → choisir le connecteur correspondant :

InfoClimat : JSON depuis API ou fichiers bruts

Weather Underground : Excel ou API selon le setup

Renseigner les paramètres spécifiques à chaque source :

Nom de la source (ex : InfoClimat_FR)

Chemin d’accès ou URL

Fréquence de synchronisation

Tester la connexion → Save

Répétez pour toutes les sources (InfoClimat, France_data, Belgique_data).


#### 3.4.2 Définir la destination S3

Ajouter une destination → choisir Amazon S3

Paramètres à remplir :

AWS Access Key ID → AWS_ACCESS_KEY_ID

AWS Secret Access Key → AWS_SECRET_ACCESS_KEY

Bucket Name → p8-meteo

Region → eu-west-3

Format → JSONL

Tester la connexion → Save


#### 3.4.3 Créer la connexion (Sync) Airbyte

Aller dans Connections → New connection

Sélectionner :

Source → la source météo définie

Destination → Amazon S3

Configurer :

Fréquence → Ex. Every hour ou Manual

Mode de chargement → Overwrite ou Append selon le besoin

Tester → Save → Sync now

Les données brutes de chaque source seront automatiquement stockées dans S3 (p8-data-path/…) en JSONL, prêtes pour la transformation Python.


## 4. Transformation des données (S3 → S3)
Objectif

Transformer les données brutes en documents JSON compatibles MongoDB, avec :

un schéma commun entre toutes les sources

la conservation maximale des informations

une structure facilement requêtable

Schéma cible (logique)
```json
{
  "source": "weather_underground | infoclimat",
  "station": { ... },
  "timestamp": "ISO-8601",
  "measurements": { ... }
}
```

Points techniques importants
Weather Underground

Les fichiers Excel contenaient une feuille par jour

La date n’est pas conservée par Airbyte

Les données sont ordonnées par heure (Time)

👉 La date est reconstruite en détectant le retour à 00:xx:xx, ce qui indique un changement de jour.

InfoClimat

Les métadonnées des stations sont extraites et intégrées

Toutes les mesures disponibles sont conservées (température, pression, pluie, neige, vent, etc.)

Les valeurs manquantes sont gérées explicitement (None ou 0 selon le cas)



## 5. Contrôle qualité des données

Un script dédié permet de mesurer la qualité des données après transformation :

Vérifications effectuées

Présence de valeurs manquantes critiques (température)

Détection de doublons (station_id + timestamp)

Calcul d’un taux d’erreur global

```yaml
Résultat obtenu
Total records        : 4950
Valeurs manquantes   : 0
Doublons             : 0
Taux d’erreur        : 0.0 %
```

Ces résultats garantissent que les données sont prêtes pour une intégration en base NoSQL.


## 6. Prérequis techniques

Environnement

Windows

Python ≥ 3.9

Compte AWS actif

Docker Desktop installé (utilisé dans les étapes suivantes)


## 7. Configuration AWS

Installation de l’AWS CLI

Télécharger et installer l’AWS CLI depuis :
https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

Configuration des credentials

Dans un terminal PowerShell :
```bash
aws configure
```

Renseigner :
```bash
AWS Access Key ID

AWS Secret Access Key

Default region name (ex : eu-west-3)

Default output format : json
```

Vérification
```bash
aws s3 ls
```

Le bucket p8-meteo doit apparaître.


## 8. Dépendances Python

requirements.txt
```bash
boto3==1.42.19
python-dateutil==2.9.0
```

Installation

Avec un environnement virtuel (recommandé) :

```bash
pip install -r requirements.txt
```


## 9. Exécution des scripts

Transformation des données
```bash
python transform_weather_s3.py
```

Résultat :
```bash
p8-processed/weather_mongodb_ready.json
```

Tests de qualité
```bash
python data_quality_checks_s3.py
```

Résultat :
```bash
p8-processed/quality_report.json
```


## 10. Conclusion de l’étape 1

À l’issue de cette étape :

Les données sont centralisées dans S3

Elles sont nettoyées, structurées et enrichies

Leur qualité est mesurée et validée

Le format est directement compatible MongoDB

👉 Le pipeline est prêt pour l’Étape 2 : intégration dans MongoDB, mise en place du schéma et des collections.


# ÉTAPE 2 — Migration des données vers MongoDB

## 1🎯 Objectif de l’étape

Cette étape consiste à importer les données météorologiques préalablement transformées (Étape 1) depuis Amazon S3 vers une base de données MongoDB, tout en :

respectant un schéma commun pour toutes les sources,

assurant la qualité et l’intégrité des données post-migration,

mettant en place des contrôles automatiques,

documentant clairement le processus.


## 2🧱 Architecture retenue

Source des données :
Amazon S3
s3://p8-meteo/p8-processed/weather_mongodb_ready.json

Base de données :
MongoDB en local (Docker / MongoDB Community)

Nom de la base :
p8_greenandcoop_forecast

Collection unique :
weather_data

👉 Le choix d’une seule collection permet :

d’unifier les requêtes,

de faciliter l’agrégation multi-sources,

de garantir un schéma homogène.


## 3📄 Format des données importées

Les données sont stockées dans un fichier JSON compatible MongoDB, contenant une liste de documents standardisés.

Structure logique d’un document :
{
  "source": "weather_underground | infoclimat",
  "station": {
    "station_id": "string",
    "name": "string",
    "latitude": float,
    "longitude": float,
    "elevation": int
  },
  "timestamp": "ISO-8601",
  "measurements": {
    "temperature_c": float,
    "humidity_pct": float,
    "pressure_hpa": float,
    "wind_speed": float,
    "wind_gust": float,
    "precip_mm": float
  }
}


Ce schéma est identique pour toutes les sources, conformément aux exigences du projet.


## 4🔁 Processus suivi (logigramme)

Le processus a été formalisé sous forme de logigramme visuel, basé sur les étapes suivantes :

- Définir sources météo dans Airbyte (étape 1)

- Définir destination S3 dans Airbyte (étape 1)

- Créer la connexion (Sync) Airbyte (étape 1)

- Airbyte collecte les données → Stockage dans S3 (étape 1)

- Lecture du fichier JSON depuis S3

- Chargement des documents en mémoire

- Connexion à MongoDB

- Insertion des documents dans la collection

- Vérifications post-import :

nombre total de documents,

doublons,

valeurs manquantes sur champs critiques

- Affichage des résultats en console


## 5 🧪 Contrôles qualité post-migration

Après l’import, le script exécute automatiquement plusieurs contrôles :

✔️ Indicateurs mesurés

Nombre total de documents importés

Nombre de doublons (station_id + timestamp)

Nombre de documents sans :

température

humidité

pression

✔️ Résultat obtenu
Total documents en base : 4950
Nombre de doublons détectés : 0
Documents sans température : 0
Documents sans humidité : 0
Documents sans pression : 0


👉 Ces résultats confirment :

l’intégrité du schéma,

l’absence de perte de données,

une migration fiable.


## 6 🐍 Script utilisé

Un script Python unique est utilisé pour :

récupérer le fichier depuis S3,

importer les données dans MongoDB,

exécuter les contrôles qualité,

afficher les résultats via des print() explicites.

Script principal
import_s3_to_mongodb.py


## 7 ▶️ Exécution du script

### 1️⃣ Pré-requis

MongoDB lancé en local (Docker ou service local)

Accès AWS configuré

Environnement Python actif

📦 Dépendances Python

Installer pymongo avec la version dans requirements.txt

Le fichier requirements.txt inclut notamment :

boto3==1.42.19
python-dateutil==2.9.0
pymongo==4.15.4


👉 pymongo est utilisé pour la communication avec MongoDB
👉 boto3 permet l’accès aux objets stockés sur S3

### 2️⃣ Commande d’exécution
python import_s3_to_mongodb.py

### 3️⃣ Résultat attendu en console
Récupération du fichier depuis S3...
Nombre de documents à importer : 4950
Documents importés avec succès : 4950

--- Vérification post-import ---
Total documents en base : 4950
Nombre de doublons détectés : 0
Documents sans température : 0
Documents sans humidité : 0
Documents sans pression : 0

--- Import terminé ---


## 8 🔍 Visualisation des données

Les données peuvent être visualisées avec MongoDB Compass :

Base : p8_greenandcoop_forecast

Collection : weather_data

Répartition observée :

Infoclimat : 1143 documents

Weather Underground (France + Belgique) : 3807 documents


# ÉTAPE 3

Conteneurisation de la migration avec Docker

## 1 🎯 Objectif de l’étape 3

L’objectif de cette étape est de conteneuriser la migration des données météo depuis Amazon S3 vers MongoDB, afin de :

- garantir la reproductibilité de l’environnement,

- isoler les composants (base de données / script de migration),

- persister les données via un volume Docker,

- démontrer une migration automatisée et fiable.


## 2 🏗️ Architecture mise en place

- 1 conteneur MongoDB
  - Image officielle mongo:7.0
  - Données persistées via un volume Docker

- 1 conteneur Python
  - Exécute un script de migration
  - Télécharge les données depuis S3
  - Insère les documents dans MongoDB
  - Effectue des contrôles qualité post-import

Les deux conteneurs communiquent via le réseau Docker Compose par défaut.


## 3 📁 Structure du projet (étape 3)

```bash
.
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── import_s3_to_mongodb_conteneur.py
```

## 4 ⚙️ Configuration des variables d’environnement

Le fichier .env (non versionné) contient :

```env
AWS_ACCESS_KEY_ID=************
AWS_SECRET_ACCESS_KEY=************
AWS_DEFAULT_REGION=eu-west-3

MONGO_URI=mongodb://mongodb:27017
```

- Les credentials AWS permettent l’accès au bucket S3

- mongodb correspond au nom du service Docker MongoDB


## 5 🐳 docker-compose.yml (résumé)

- MongoDB exposé sur le port local 27021

- Volume Docker pour persister les données

- Conteneur Python dépendant de MongoDB

MongoDB reste accessible depuis l’hôte via MongoDB Compass :

```bash
mongodb://localhost:27021
```

## 6 📦 Volume Docker

Un volume nommé est utilisé :

```bash
projet8_projet_8_mongo_data
```

Il garantit que les données MongoDB sont conservées même après :

```bash
docker compose down
```

## 7 🧠 Script de migration

Le script import_s3_to_mongodb_conteneur.py effectue :

- 1) Connexion à Amazon S3

- 2) Téléchargement du fichier JSON final :

```bash
p8-meteo/p8-processed/weather_mongodb_ready.json
```

- 3) Insertion des documents dans MongoDB

- 4) Contrôles qualité post-import :
  - Nombre total de documents
  - Doublons (station_id + timestamp)
  - champs critiques manquants (température, humidité, pression)


## 8 ▶️ Commandes à exécuter
🔹 Build + lancement complet initial
```bash
docker compose up --build
```
🔹 Lancement sans rebuild
```bash
docker compose up
```
🔹 Arrêt des services
```bash
docker compose down
```
🔹 Vérifier les volumes
```bash
docker volume ls
```
🔹 Vérifier les conteneurs
```bash
docker ps -a
```
🔹 Inspecter un volume en particulier :
```bash
docker volume inspect projet_8_mongo_data
```

## 9 🔍 Vérifications attendues

Logs affichant :

```bash
Documents importés avec succès : 4950
```

MongoDB Compass :

- Base : p8_greenandcoop_forecast

- Collection : weather_data

- 4950 documents présents

Données toujours présentes après redémarrage


## 10 ✅ Résultat

Migration automatisée et reproductible

Environnement isolé via Docker

Données persistées

Qualité des données contrôlée

👉 Cette étape valide la conteneurisation complète de la chaîne de migration.