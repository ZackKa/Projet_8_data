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
```bash

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
```bash

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