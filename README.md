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

## Version avec replication

### création des dossier pour simuler serveur en local

- lancer les serveurs avec : 
```bash
mongod --replSet rs0 --port 28019 --dbpath "C:\...\data\rs0-3"
```
- Aller sur serveur 1 avec mongosh --port 28017 puis lancer initialisation :
```bash
rs.initiate({
...   _id: "rs0",
...   members: [
...     { _id: 0, host: "localhost:28017" },
...     { _id: 1, host: "localhost:28018" },
...     { _id: 2, host: "localhost:28019" }
...   ]
... })
```
- lancer le script d'import des données.
- verifier sur mongosh le nombre de document avec :
```bash
use p8_greenandcoop_forecast
db.weather_data.countDocuments()
```
Vérifiaction possible aussi sur compass avec les bon port

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

## Version avec replication.

-Lancer sur le path du projet :
```bash
docker compose up -d --build mongo1 mongo2 mongo3
```
puis dans un nouveau terminal :
```bash
docker exec -it mongo1_p8 mongosh
```
initiate avec :
```bash
rs.initiate({
...   _id: "rs0",
...   members: [
...     { _id: 0, host: "mongo1_p8:27017" },
...     { _id: 1, host: "mongo2_p8:27017" },
...     { _id: 2, host: "mongo3_p8:27017" }
...   ]
... })
```
Verifier les primary et secondary avec :
```bash
rs.status()
```
Puis lancer l'import des données avec :
```bash
docker compose up --build -d python-migration
```
Verifier le nombre de données sur chaque serveur mongo avec :
```bash
use p8_greenandcoop_forecast
db.weather_data.countDocuments()
```



# 🚀 Étape 4 — Déploiement MongoDB sur AWS ECS, reporting et sauvegardes

## 1 🎯 Objectif de l’étape

L’objectif de cette étape est de déployer la base de données MongoDB dans le cloud AWS afin de :

- reproduire l’architecture de migration dans un environnement distant,

- rendre la base accessible à distance de manière sécurisée,

- importer les données météo depuis Amazon S3 (source de vérité),

- mesurer les performances d’accès aux données,

- mettre en place une stratégie de sauvegarde,

- assurer la supervision via des logs centralisés.

Cette étape valide la capacité à industrialiser la chaîne data dans un environnement cloud.


## 2 🧱 Contexte et prérequis

À l’issue de l’Étape 3 :

Les données météo (≈ 4950 documents) sont :

- collectées via Airbyte,

- transformées,

- stockées dans Amazon S3.

Le fichier final utilisé est :
```bash
s3://p8-meteo/p8-processed/weather_mongodb_ready.json
```

MongoDB fonctionne et est maîtrisé :

- en local,

- en environnement Docker.

L’import S3 → MongoDB est automatisé via un script Python.

👉 L’Étape 4 consiste à transposer cette architecture vers AWS, sans modifier la logique data.


## 3 🏗 Architecture cible

Architecture déployée :

```sql
[Poste local]
     |
     | (script Python)
     v
[S3 - p8-meteo]
     |
     v
[MongoDB conteneurisé sur ECS Fargate]
     |
     +--> CloudWatch Logs
     |
     +--> Sauvegardes MongoDB vers S3
```

Choix techniques :

Amazon ECS Fargate : exécution de conteneurs sans gestion d’instances EC2

MongoDB officiel (mongo:7.0) : cohérence avec les étapes précédentes

S3 :

- stockage des données sources,

- stockage des sauvegardes


## 🧩 Phase 1 — Création de l’infrastructure AWS

### Objectif de la partie AWS

Déployer une infrastructure MongoDB dans le cloud respectant les contraintes suivantes :

Hébergement sur AWS

Utilisation de conteneurs / services AWS

Mise en place de la réplication MongoDB

Importation des données météo depuis Amazon S3

Mesure des performances (temps d’accès)

Mise en place des sauvegardes

Configuration du monitoring et des logs

## 4 ☁️ Infrastructure AWS mise en place
### 4.1 Région AWS

Région utilisée :
```bash
eu-west-3 (Paris)
```

Justification :

- cohérence avec les buckets S3,

- faible latence,

- conformité RGPD.

⚠️ Les régions utilisées par Airbyte ou S3 n’impactent pas ECS tant que les permissions IAM sont correctes.


## 4.2️ Création du cluster ECS

Mode pas-à-pas :

- Connecte-toi à la console AWS → Recherche ECS → Clique sur Clusters → Create Cluster

- Sélectionne Networking only (Fargate)

- Clique sur Next step

 - Nom du cluster : p8-mongodb-cluster-v2

- Laisse les autres paramètres par défaut (VPC, subnets, etc.)

- Clique sur Create

Justification Fargate :

- Pas de gestion de serveur EC2

- Scalabilité automatique

- Idéal pour un projet Data orienté cloud

## 4.3️ Task Definition MongoDB

Mode pas-à-pas :

- Dans la console ECS → Task Definitions → Create new Task Definition

- Choisir Fargate → Next step

- Nom de la Task : p8-mongodb-task

- Task Role : None (ou ecsTaskExecutionRole par défaut)

- Network Mode : awsvpc

- Container Definitions → Add container

- Container name : mongodb

- Image : mongo:7.0

- Memory Limits : 512 MiB (minimum suffisant pour le projet)

- Port mappings : Container port 27017

Storage and Logging :

- Enable CloudWatch Logs

- Log group : /ecs/mongodb-task-p8

- Stream prefix : mongo

- Region : eu-west-3

Clique sur Add puis Create pour finaliser la Task Definition

Notes :

- Le port 27017 est le port standard MongoDB

- Les logs sont visibles en temps réel dans CloudWatch

## 4️.4 Sécurité réseau

Mode pas-à-pas :

Aller dans EC2 → Security Groups

Créer un nouveau Security Group : mongodb-sg

Ajouter une règle entrante :

Type : Custom TCP Rule

Port : 27017

Source : IP de ton PC (x.x.x.x/32)

Associer ce Security Group à la Task ECS lors du lancement

## 4.5️ Lancement de la Task ECS

Mode pas-à-pas :

Dans ECS → Clusters → p8-mongodb-cluster-v2

Clique sur Tasks → Run Task

Launch type : Fargate

Cluster VPC : choisir le VPC par défaut

Subnet : sélectionner un subnet public

Assign public IP : Enabled

Security group : mongodb-sg

Task Definition : p8-mongodb-task

Clique sur Run Task

📌 Une fois la Task lancée, tu peux récupérer l’IP publique dans la colonne Public IP pour te connecter depuis MongoDB Compass ou tes scripts Python :

mongodb://<IP_PUBLIQUE_ECS>:27017


## 3️⃣ Architecture finale : MongoDB répliqué sur EC2 (remplacement de la partie fargate)
### 3.1 Création des instances EC2

3 instances EC2

- OS : Ubuntu 22.04 LTS

- Type : t3.micro (free tier compatible)

- Même VPC

- Même Security Group

Ports ouverts :

- 22 (SSH)

- 27017 (MongoDB)

- Autorisation entre instances EC2

Lancer les instances avec cette commande pour chacune (à adapter) :
```bash
ssh -i "(mon-chemin)\ma-key.pem" ubuntu@(ip-du-ec2)
```

Sur chaque instance :
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y gnupg curl
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
```
verification d'instalation mongo et active au demarage avec :
```bash
mongod --version
sudo systemctl start mongod
sudo systemctl enable mongod
```

Verification du status, doit avoir active avec :
```bash
sudo systemctl status mongod
```

Activation du replica set dans :
```bash
sudo nano /etc/mongod.conf
```
```bash
replication:
  replSetName: rs0
```
```bash
sudo systemctl restart mongod
sudo systemctl enable mongod
```

## 4️⃣ Mise en place du Replica Set MongoDB

Depuis l’instance primaire :
```bash
mongosh
```
A la suite de "test>" :
```bash
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "IP-PRIVEE-EC2-1:27017" },
    { _id: 1, host: "IP-PRIVEE-EC2-2:27017" },
    { _id: 2, host: "IP-PRIVEE-EC2-3:27017" }
  ]
})
```

Vérification :
```bash
rs.status()
```
✔️ 1 Primary
✔️ 2 Secondary

## 5️⃣ Importation des données depuis Amazon S3
### 5.1 Script d’import Python

Script exécuté depuis une EC2

Connexion MongoDB via URI Replica Set

MONGO_URI = "mongodb://IP1:27017,IP2:27017,IP3:27017/?replicaSet=rs0"


Fonctionnalités du script :

Lecture JSON depuis S3

Insertion dans MongoDB

Vérification :

nombre de documents

doublons

champs critiques manquants

✔️ 4950 documents importés
✔️ Répliqués automatiquement sur les 3 nœuds

Pour lancer le script depuis ec2 :
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install boto3==1.42.19 python-dateutil==2.9.0 pymongo==4.15.4 python-dotenv==1.1.0
```
Ensuite depuis un autre terminal non connecter sur ec2 mais depuis le poste local :
```bash
# script migration donnees
scp -i "path-de-ma-key.pem" "path-de-mon-fichier\import_s3_to_aws_ECS.py" ubuntu@(ip-prive):~/
# on peux mettre le .env pour un exercice
scp -i "path-de-ma-key.pem" "path-de-mon-fichier\.env" ubuntu@(ip-prive):~/
```
On repart sur le terminal EC2 :
```bash
#Verification de l'import du script
ls -l ~/
#Verification des bases mongo
python3 -c "from pymongo import MongoClient; import os; client = MongoClient(os.getenv('MONGO_URI_AWS')); print(client.list_database_names())"
['admin', 'config', 'local']
#Import des credentials pour que le script fonctionne
export AWS_ACCESS_KEY_ID=*******
export AWS_SECRET_ACCESS_KEY=******
#Lancer le script
python3 import_s3_to_aws_ECS.py
```
Doit retourner :
```bash
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
```
### 5.2 Vérification des document dans chaque ec2

Dans le terminal EC2 on entre dans mongosh avec :
```bash
mongosh
# On se connecte à la base
use p8_greenandcoop_forecast
# On compte le nombre de document
db.weather_data.countDocuments()
# Doit retourner 4950
```

## 6️⃣ Sauvegarde des données MongoDB
### 6.1 Script de sauvegarde

Utilisation de mongodump

Export compressé .gz

Upload automatique vers S3

mongodump --uri "mongodb://IP1,IP2,IP3/?replicaSet=rs0" --archive=backup.gz --gzip

Pour ça, dans le terminal connecté au primary EC2 on fait :
```bash
#instaler mongodump
sudo apt install -y mongodb-database-tools
mongodump --version
```
Dans un terminal en local on instal le script de sauvegarde dans ec2 avec :
```bash
scp -i "path-de-ma-key.pem" "path-de-mon-fichier\backup_mongodb_to_s3.py" ubuntu@(ip-prive):~/

```
On repart sur le terminal EC2 :
```bash
#Import des credentials pour que le script fonctionne
export AWS_ACCESS_KEY_ID=*******
export AWS_SECRET_ACCESS_KEY=******
python3 backup_mongodb_to_s3.py
```

✔️ Sauvegarde locale
✔️ Sauvegarde externalisée sur S3
✔️ Historisation par timestamp

## 7️⃣ Monitoring et logs
### 7.1 CloudWatch

Monitoring automatique des instances EC2 :

CPU

Réseau

Disque

Statut des instances

8.2 Logs MongoDB

Logs locaux :

/var/log/mongodb/mongod.log

Logs AWS :

EC2 Metrics via CloudWatch

🎯 Objectif atteint :

Surveillance de la santé

Détection d’incidents

Traçabilité des opérations

### 7.2 log mongo dans cloud watch

### Objectif

Mettre en place un monitoring centralisé des logs et métriques de MongoDB sur plusieurs instances EC2 via Amazon CloudWatch.

### Pourquoi faire du monitoring ?

- Détecter rapidement les problèmes (CPU élevé, saturation disque, erreurs MongoDB…).

- Analyser les performances pour optimiser l’infrastructure.

- Avoir un historique des logs et métriques pour les audits et débogages.

- CloudWatch centralise toutes les informations depuis tes instances EC2 et fournit :

  - Logs en temps réel

  - Alertes (alarmes)

  - Graphiques de métriques (CPU, RAM, disque, réseau)

  - Analyse avancée via Logs Insights et métriques personnalisées

### Prérequis

- 3 instances EC2 Ubuntu 22.04 avec MongoDB installé.

- Accès IAM avec permissions pour créer un rôle et attacher CloudWatch Agent.

- Accès à AWS CloudWatch (console).

### Étape 1 — Vérifier les logs MongoDB

Sur chaque EC2, vérifier que MongoDB fonctionne et que les logs existent :

```bash
ls -l /var/log/mongodb/
sudo tail -f /var/log/mongodb/mongod.log
```

On doit voir des lignes de logs comme : WiredTiger message et client metadata.

### Étape 2 — Créer un rôle IAM pour EC2

1 - Dans AWS → IAM → Roles → Create role

2 - Sélectionner Service AWS → EC2

3 - Choisir Use case → EC2 (Allows EC2 instances to call AWS services on your behalf)

4 - Ajouter la politique gérée : CloudWatchAgentServerPolicy

5 - Nommer le rôle : EC2-CloudWatch-Mongo-P8

6 - Créer le rôle

### Étape 3 — Attacher le rôle IAM aux instances EC2

Pour chaque EC2 :

- EC2 → Actions → Security → Modify IAM role

- Sélectionner le rôle EC2-CloudWatch-Mongo-P8

- Appliquer et attendre 1–2 minutes pour que le rôle soit actif

💡 Le rôle IAM permet à CloudWatch Agent sur l’EC2 de publier des logs et métriques dans le compte AWS sans stocker de credentials directement sur l’instance.

### Étape 4 — Installer CloudWatch Agent

Sur chaque EC2 :

Mettre à jour les paquets et télécharger le package :

```bash
sudo apt update
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

Vérifier l’outil :
```bash
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -h
```

### Étape 5 — Configurer CloudWatch Agent

Créer ou vérifier le fichier de configuration JSON pour MongoDB :
```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

Coller :
```bash
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/mongodb/mongod.log",
            "log_group_name": "/p8/mongodb/logs",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S.%f"
          }
        ]
      }
    }
  },
  "metrics": {
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["/"]
      }
    }
  }
}
```
puis ctrl+o , entrée, ctrl+x

Démarrer et appliquer la configuration :
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
-a fetch-config \
-m ec2 \
-c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
-s
```

Vérifier que le service est actif :
```bash
sudo systemctl status amazon-cloudwatch-agent
```

On doit voir Active: active (running).

💡 Cette étape permet à CloudWatch Agent de collecter et envoyer les logs MongoDB et les métriques système dans CloudWatch.

### Étape 6 — Vérifier les logs et métriques sur CloudWatch
Logs

- AWS → CloudWatch → Logs → Groupe /p8/mongodb/logs

- Vérifier les flux de journaux pour chaque instance EC2 (i-xxxx)

- Cliquer sur un flux → Voir les logs en temps réel

Metrics

- AWS → CloudWatch → Metrics → EC2 → Per-Instance Metrics

- Vérifier :

  - CPU Utilization

  - Memory

  - Disk

  - Network

Résultat attendu

- Les 3 EC2 envoient leurs logs MongoDB dans CloudWatch.

- Les métriques système sont visibles par instance.

- Possibilité de créer alertes et dashboards pour suivre l’état en temps réel.

Points 

- Monitoring = visibilité sur l’infrastructure.

- CloudWatch centralise logs + métriques.

- Permet de réagir rapidement aux problèmes et d’optimiser les ressources.

- Séparation des permissions via IAM roles pour plus de sécurité.

## 8 Accès aux données 

On copie le script dans l'instance EC2
```bash
scp -i "ec2-mongo-key.pem" "measure_access_time_ecs.py" ubuntu@<IP_DU_PRIMARY>:~/
```
Dans l'EC2 connecté on fait :
```bash
python3 --version
python3 -m pip install pymongo
```
On lance le script :
```bash
python3 measure_access_time_ecs.py

```



## 📥 Phase 2 — Import des données depuis S3 vers MongoDB ECS

## 5 🎯 Principe

👉 Les données ne sont pas copiées depuis MongoDB local
👉 Elles sont réimportées proprement depuis S3, source de vérité du projet.

Script utilisé : import_s3_to_aws_ECS.py
Rôle du script

Lire le fichier JSON depuis S3

Insérer les documents dans MongoDB ECS

Vérifier :

- nombre de documents ;

- doublons ;

- valeurs critiques manquantes

```bash
Configuration MongoDB
MONGO_URI_AWS = os.getenv(
    "MONGO_URI_AWS",
    "mongodb://<IP_PUBLIQUE_ECS>:27017"
)
```

➡️ Le script est exécuté en local, ce qui est explicitement autorisé par l’énoncé.

Commande d’exécution
```bash
python import_s3_to_aws_ECS.py
```
Résultat obtenu
```bash
4950 documents importés

0 doublon

0 valeur critique manquante
```
Données visibles dans MongoDB Compass

## ⏱ Phase 3 — Mesure du temps d’accessibilité aux données

## 6 🎯 Objectif

Mesurer le temps réel d’exécution d’une requête MongoDB sur une base distante hébergée sur AWS.

Principe : 

- Script Python exécuté en local

- Connexion à MongoDB ECS

- Requête ciblée :

 - une date ;

 - une station ;

- Mesure via time.perf_counter()

Exemple de métrique
Temps d’exécution de la requête : 0.320 secondes


👉 Résultat exploitable dans le reporting.

## 💾 Phase 4 — Sauvegarde de la base MongoDB
## 7 🎯 Objectif

Mettre en place une stratégie de sauvegarde cloud fiable et reproductible.

Outil utilisé :
```bash
mongodump
```

Installation locale

Ajout au PATH système Windows

Commande exécutée dans le script
```bash
mongodump \
  --uri="mongodb://<IP_PUBLIQUE_ECS>:27017" \
  --archive="mongodb_backup_2026-01-05_14-06-15.gz" \
  --gzip
```

Résultat
```bash
done dumping p8_greenandcoop_forecast.weather_data (4950 documents)
```

Upload du backup vers S3
```bash
aws s3 cp mongodb_backup_2026-01-05_14-06-15.gz \
s3://p8-meteo/p8-backups/mongodb/
```

Emplacement final
```bash
s3://p8-meteo/p8-backups/mongodb/mongodb_backup_2026-01-05_14-06-15.gz
```

📌 La sauvegarde est :

- horodatée ;

- externalisée ;

- restaurable.

## 📊 Phase 5 — Monitoring & logs

## 8 Logs MongoDB

Les logs MongoDB sont centralisés dans AWS CloudWatch

Les logs comprennent :

- connexions ;

- interruptions ;

- performances ;

- état du conteneur

👉 Cette supervision répond aux exigences de surveillance cloud.

✅ Validation finale

Élément	                 Statut

MongoDB sur ECS	         ✅
Accès distant	           ✅
Import S3 → MongoDB	     ✅
Temps d’accessibilité    ✅
Sauvegarde S3	           ✅
Logs & monitoring	       ✅

✅ Validation finale

| Exigence du projet                        | Validation  |
|:------------------------------------------|:----------- |
| Déploiement MongoDB sur AWS ECS           | ✅         |
| Accès distant sécurisé                    | ✅         |
| Import des données depuis S3 dans MongoDB | ✅         |
| Mesure du temps d’accès                   | ✅         |
| Sauvegarde cloud dans S3                  | ✅         |
| Monitoring et logs                        | ✅         |