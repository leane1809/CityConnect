# CityConnect — VilleSignal

Application web de signalement citoyen des problèmes urbains.

CityConnect, présenté sous le nom **VilleSignal** dans l'interface, permet aux citoyens de signaler des problèmes urbains, de suivre leur traitement et de consulter les signalements géolocalisés. Les agents peuvent consulter les signalements relevant de leur service et enregistrer les interventions effectuées.

> **Projet académique** — adapter cette documentation aux consignes exactes de l'enseignant et à la configuration réelle de l'environnement avant la remise.

## Sommaire

- [Objectifs](#objectifs)
- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Lancement](#lancement)
- [Données et base de données](#données-et-base-de-données)
- [Sécurité](#sécurité)
- [Carte et géolocalisation](#carte-et-géolocalisation)
- [Tests manuels](#tests-manuels)
- [Structure du projet](#structure-du-projet)
- [Dépannage](#dépannage)
- [Améliorations possibles](#améliorations-possibles)

## Objectifs

Les problèmes urbains — par exemple les dépôts d'ordures, les routes endommagées ou les problèmes d'éclairage — peuvent être difficiles à signaler et à suivre. VilleSignal propose un point d'entrée web pour enregistrer ces problèmes et faciliter le suivi des actions des services concernés.

## Fonctionnalités

### Espace citoyen

- Soumettre un signalement avec une catégorie, un quartier, une adresse ou un repère, une description et un numéro de téléphone.
- Joindre une photo au format JPG/JPEG ou PNG, avec une limite de taille définie par l'application.
- Recevoir un code de suivi après l'enregistrement.
- Consulter les informations de suivi disponibles à partir du code.
- Soutenir un signalement existant avec la fonctionnalité « Moi aussi », lorsque celle-ci est activée.
- Consulter les signalements publics récents.

### Géolocalisation et carte

- Choisir une position sur une carte lors de la création d'un signalement.
- Enregistrer la latitude et la longitude dans la base de données.
- Afficher sur la carte publique les signalements qui disposent de coordonnées valides.
- Consulter les informations d'un marqueur et filtrer les résultats par catégorie, quartier ou statut.

Les signalements créés avant l'ajout des coordonnées peuvent ne pas apparaître sur la carte. Leurs coordonnées ne sont pas générées automatiquement.

### Espace agents

- Connexion des agents.
- Consultation des signalements relevant du service de l'agent, selon les règles d'accès implémentées.
- Enregistrement d'une intervention, d'un commentaire et d'un nouveau statut.
- Gestion des statuts prévus par l'application : `nouveau`, `en cours`, `résolu` et `rejeté`.
- Enregistrement d'un motif en cas de rejet, si cette fonctionnalité est activée dans l'interface.

### Statistiques

L'application prévoit des indicateurs tels que :

- Répartition des signalements par catégorie et par quartier.
- Signalements non résolus depuis plus de sept jours.
- Évolution hebdomadaire du nombre de signalements.
- Délai moyen de résolution par service.

La disponibilité des indicateurs dépend des données enregistrées et de la route de statistiques de l'application.

## Technologies

| Élément | Technologie |
|---|---|
| Langage serveur | Python |
| Framework web | Flask |
| Base de données | SQLite |
| Interface | HTML, CSS et JavaScript avec les templates Jinja |
| Cartographie | Leaflet et fonds OpenStreetMap |
| Protection CSRF | Flask-WTF |
| Traitement des images | Pillow |
| Hachage des mots de passe | Werkzeug |

Leaflet et OpenStreetMap sont chargés depuis des services externes dans les pages qui affichent une carte ; une connexion Internet est donc nécessaire pour charger les tuiles cartographiques.

## Prérequis

- Windows, macOS ou Linux.
- Python 3 installé.
- `pip` disponible.
- Un navigateur web moderne.
- Une connexion Internet pour charger les fonds de carte.

Les commandes ci-dessous sont données pour **Windows PowerShell**, depuis le dossier du projet.

## Installation

### 1. Ouvrir le dossier du projet

Dans PowerShell :

```powershell
cd "C:\Users\Leane NTAKEU\CityConnect"
```

### 2. Créer un environnement virtuel

Si le dossier `.venv` n'existe pas encore :

```powershell
py -m venv .venv
```

Activer l'environnement :

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l'activation, il est possible d'utiliser directement l'interpréteur de l'environnement virtuel pour exécuter les commandes Python. Ne modifiez pas les règles de sécurité de PowerShell sans en comprendre les conséquences.

### 3. Installer les dépendances

Si le projet possède déjà un fichier `requirements.txt` :

```powershell
python -m pip install -r requirements.txt
```

Si ce fichier n'existe pas encore, installez les bibliothèques réellement utilisées par l'application, puis créez le fichier de dépendances. Les imports visibles dans le code du projet indiquent notamment Flask, Flask-WTF et Pillow :

```powershell
python -m pip install Flask Flask-WTF Pillow
python -m pip freeze > requirements.txt
```

> Si le projet utilise d'autres bibliothèques, vérifiez les imports de `app.py` et ajoutez-les aux dépendances avant de générer `requirements.txt`. Pour un rendu reproductible, conservez un fichier de dépendances validé dans le dépôt.

### 4. Vérifier les fichiers essentiels

À la racine du projet, vérifiez la présence des éléments utilisés par l'application, notamment :

- `app.py`
- `projet.db`
- `templates/`
- `static/`
- `static/uploads/` (créé par l'application ou à créer selon sa configuration)
- `requirements.txt` (recommandé)

Ne créez pas une nouvelle base de données par-dessus `projet.db` si elle contient déjà les données de travail.

## Configuration

### Clé secrète Flask

L'application utilise une clé secrète pour les sessions et la protection CSRF. Définissez une valeur privée dans l'environnement plutôt que d'utiliser une valeur connue en production.

Dans PowerShell, pour la session courante :

```powershell
$env:FLASK_SECRET_KEY = "remplacer-par-une-cle-longue-et-aleatoire"
```

Utilisez une vraie valeur aléatoire, gardez-la confidentielle et ne la publiez jamais dans Git. Cette commande ne conserve la variable que dans la session PowerShell courante. Vérifiez dans `app.py` le nom exact de la variable d'environnement lue par votre configuration Flask, car le projet peut également contenir une configuration `SECRET_KEY` distincte.

### Base de données

Le chemin de la base est défini dans `app.py`. Dans la version du projet décrite ici, le fichier SQLite est `projet.db`, situé à la racine du projet.

Avant une modification du schéma ou une migration :

1. Arrêter le serveur si nécessaire.
2. Faire une copie de sauvegarde de `projet.db`.
3. Exécuter uniquement le script de migration prévu.
4. Vérifier que les tables et les données sont toujours présentes.

Ne supprimez pas la base pour résoudre une erreur de migration.

### Compte agent

Les comptes d'agent doivent être créés avec un mot de passe haché et une méthode d'administration prévue par le projet. N'inscrivez jamais un vrai mot de passe dans ce README. Pour une démonstration, utilisez uniquement des comptes de test autorisés et communiquez leurs identifiants de façon séparée et sécurisée.

## Lancement

Depuis le dossier du projet, avec l'environnement virtuel activé :

```powershell
python app.py
```

Ouvrez ensuite l'adresse locale indiquée par Flask dans le terminal, généralement :

```text
http://127.0.0.1:5000/
```

Pages et routes utiles si elles sont présentes dans la version exécutée :

| Adresse | Utilité |
|---|---|
| `/` | Accueil et liste des signalements récents |
| `/signaler` | Formulaire de signalement |
| `/carte` | Carte publique des signalements géolocalisés |
| `/api/carte-signalements` | Données JSON utilisées par la carte |
| `/api/statistiques` | Données statistiques, si cette route est activée |

Les autres routes, notamment la connexion, le suivi et l'espace agent, peuvent dépendre des noms exacts définis dans `app.py`.

## Données et base de données

La base contient les principales tables suivantes :

- `categories` : catégories et services responsables.
- `quartiers` : quartiers proposés dans le formulaire.
- `agents` : comptes et services des agents.
- `signalements` : descriptions, adresses, photos, dates, statuts et codes de suivi.
- `interventions` : actions effectuées par les agents sur les signalements.
- `soutiens` : soutiens citoyens, si le bonus « Moi aussi » a été installé.

Les colonnes `latitude` et `longitude` ont été ajoutées à `signalements` par migration. Elles sont facultatives afin de préserver les signalements historiques qui n'ont pas de position GPS.

Le jeu de données de développement a été vérifié à un moment donné avec les volumes suivants : 5 catégories, 12 quartiers, 8 agents, 200 signalements et 250 interventions. Ces nombres peuvent évoluer au cours des tests ; relancez le script de vérification pour confirmer l'état actuel avant la remise.

## Sécurité

Les protections ci-dessous doivent être vérifiées dans le code et pendant les tests avant de présenter l'application comme sécurisée.

- **CSRF :** formulaires protégés avec un jeton CSRF lorsque la protection Flask-WTF est activée.
- **SQL :** utiliser des requêtes paramétrées plutôt que de concaténer les valeurs fournies par l'utilisateur dans les requêtes.
- **Mots de passe :** stocker des hachages de mots de passe, jamais les mots de passe en clair.
- **Photos :** contrôler le type réel du fichier côté serveur, limiter sa taille, générer un nom de fichier côté serveur et ne pas faire confiance uniquement à l'extension.
- **Validation :** vérifier les champs côté serveur, y compris les identifiants de catégorie et de quartier et les coordonnées GPS.
- **Contrôle d'accès :** vérifier côté serveur qu'un agent ne peut consulter ou modifier que les signalements autorisés pour son service.
- **Erreurs :** ne pas afficher de traces de débogage ou d'informations internes aux utilisateurs en production.
- **Secrets :** ne pas publier les clés secrètes, mots de passe, fichiers `.env` ou identifiants réels.
- **Sauvegardes :** conserver une copie de la base avant les migrations et les opérations importantes.

### Mode développement et production

Le serveur de développement Flask est destiné aux tests locaux, pas à l'hébergement public. Avant un déploiement, désactivez le mode debug, utilisez une clé secrète forte, configurez un serveur de production et vérifiez les paramètres de sécurité et les sauvegardes.

## Tests manuels

Effectuez les tests suivants avant le rendu et notez le résultat observé.

- [ ] La page d'accueil se charge.
- [ ] Un citoyen peut envoyer un signalement valide.
- [ ] Une description de moins de 20 caractères est refusée.
- [ ] Une catégorie ou un quartier invalide est refusé côté serveur.
- [ ] Une photo valide est acceptée et une photo non autorisée est refusée.
- [ ] Une photo dépassant la limite de taille est refusée.
- [ ] Un code de suivi est fourni après la création d'un signalement.
- [ ] Le suivi retrouve le bon signalement.
- [ ] Un agent peut se connecter avec un compte de test valide.
- [ ] Les restrictions d'accès par service sont respectées.
- [ ] Une intervention met à jour le statut attendu.
- [ ] Le soutien « Moi aussi » empêche les doublons selon la règle définie.
- [ ] Un signalement avec coordonnées valides apparaît sur `/carte`.
- [ ] Un signalement sans coordonnées n'est pas placé à un endroit fictif.
- [ ] Les filtres de la carte fonctionnent.
- [ ] Les statistiques s'affichent avec les données disponibles.
- [ ] Une URL inexistante affiche une page d'erreur appropriée.
- [ ] L'application ne démarre pas en mode debug pour la configuration de production.

## Structure du projet

Structure indicative : adaptez-la aux fichiers réellement présents dans le dépôt.

```text
CityConnect/
├── app.py
├── projet.db
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── signaler.html
│   └── carte.html
├── static/
│   └── uploads/
├── schema.sql
├── verifier_donnees.py
├── ajouter_moi_aussi.py
└── ajouter_coordonnees.py
```

D'autres templates, scripts ou fichiers statiques peuvent exister dans votre version. Ne supprimez pas de fichiers qui ne figurent pas dans cet exemple sans vérifier leur utilité.

## Dépannage

### `ModuleNotFoundError`

Vérifiez que l'environnement virtuel est activé, puis installez les dépendances :

```powershell
python -m pip install -r requirements.txt
```

### La carte est vide

- Vérifiez la connexion Internet.
- Vérifiez que `/api/carte-signalements` renvoie du JSON.
- Vérifiez qu'au moins un signalement possède une latitude et une longitude valides.
- Consultez la console du navigateur et le terminal Flask en cas d'erreur.

### Erreur CSRF

Vérifiez que chaque formulaire POST inclut un jeton CSRF valide et que la clé secrète Flask est correctement configurée. Ne désactivez pas globalement la protection CSRF pour contourner le problème.

### La base de données est introuvable

Vérifiez que vous lancez `app.py` depuis le bon projet et que le chemin de `projet.db` dans la configuration correspond à son emplacement.

### Une photo ne s'enregistre pas

Vérifiez le format réel du fichier, sa taille et les droits d'écriture sur le dossier `static/uploads/`.

## Améliorations possibles

- Ajouter des tests automatisés pour les routes et les permissions.
- Améliorer la gestion des sauvegardes et des migrations.
- Ajouter une pagination aux listes de signalements.
- Ajouter une recherche plus avancée et des filtres dans les listes.
- Améliorer l'accessibilité et l'affichage sur mobile.
- Prévoir une procédure de déploiement avec serveur de production et configuration sécurisée.
- Ajouter des tests de bout en bout pour la carte et le parcours complet de signalement.

---

**Projet :** CityConnect / VilleSignal  
**Cadre :** projet académique  
**Dernière mise à jour :** à compléter avant la remise.
