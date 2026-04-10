# NumStore - Boutique de Produits Numériques

Application FastAPI avec PostgreSQL, templates Jinja2 et paiement **Paystack** (Afrique de l'Ouest).

## Structure du Projet

```
numstore/
├── server.py           # Point d'entrée FastAPI
├── database.py         # Configuration PostgreSQL (asyncpg)
├── auth.py             # Authentification JWT admin
├── email_utils.py      # Envoi d'emails (Resend)
├── models.py           # Modèles Pydantic
├── routes/
│   ├── __init__.py
│   ├── pages.py        # Routes des pages (templates)
│   ├── products.py     # API produits
│   ├── payments.py     # API paiements (Paystack)
│   ├── access.py       # API codes d'accès
│   ├── portfolio.py    # API portfolios
│   └── admin.py        # API admin
├── templates/          # Templates Jinja2
├── static/css/         # Styles CSS
├── requirements.txt
├── schema.sql          # Schema PostgreSQL
├── products.sql        # Données initiales produits
├── render.yaml         # Configuration Render
└── .env.example
```

## Déploiement sur Render

### Option 1: Blueprint (Automatique)

1. Créez un compte sur [Render](https://render.com)
2. Connectez votre repository GitHub
3. Créez un nouveau "Blueprint" et pointez vers le fichier `render.yaml`
4. Render créera automatiquement la base de données et le service web

### Option 2: Manuel

#### Étape 1: Créer la base de données PostgreSQL
1. Dashboard Render → New → PostgreSQL
2. Nom: `numstore-db`
3. Plan: Free
4. Créez la base de données
5. Notez les informations de connexion

#### Étape 2: Initialiser le schema
```bash
psql -h <HOST> -U <USER> -d <DB_NAME> -f schema.sql
psql -h <HOST> -U <USER> -d <DB_NAME> -f products.sql
```

#### Étape 3: Créer le Web Service
1. Dashboard Render → New → Web Service
2. Connectez votre repository
3. Configurez:
   - **Name**: numstore
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

#### Étape 4: Variables d'environnement

```
DB_HOST=<host from postgres>
DB_NAME=<dbname from postgres>
DB_PORT=5432
DB_PWD=<password from postgres>
DB_USER=<user from postgres>
SECRET_KEY=<générez une clé secrète>
ADMIN_PASSWORD=<mot de passe admin>
PAYSTACK_SECRET_KEY=<votre clé secrète Paystack>
RESEND_API_KEY=<votre clé Resend>
SENDER_EMAIL=onboarding@resend.dev
```

## Configuration Paystack

1. Créez un compte sur [Paystack](https://dashboard.paystack.com)
2. Allez dans **Settings → API Keys & Webhooks**
3. Copiez votre **Secret Key** (commence par `sk_test_` ou `sk_live_`)
4. Configurez le **Webhook URL** : `https://votre-app.onrender.com/api/payment/webhook`

### Devises supportées
- **XOF** (Franc CFA) - Côte d'Ivoire, Sénégal, etc.
- **NGN** (Naira) - Nigeria
- **GHS** (Cedi) - Ghana
- **ZAR** (Rand) - Afrique du Sud
- **USD** (Dollar US)

## Commandes de Build et Start

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

## Développement Local

1. Créez un fichier `.env` basé sur `.env.example`
2. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez l'application:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

## Fonctionnalités

- **Boutique** : Produits numériques et services portfolio
- **Paiement** : Intégration Paystack (XOF/CFA, Mobile Money supporté)
- **Codes d'accès** : Système de codes temporaires pour téléchargement (6h)
- **Portfolio** : Formulaire de création de portfolio avec workflow de validation
- **Admin** : Dashboard de gestion des produits et soumissions
- **Emails** : Notifications automatiques via Resend

## API Endpoints

### Paiements
- `POST /api/payment/create-session` - Créer une session de paiement
- `GET /api/payment/status/{reference}` - Vérifier le statut
- `POST /api/payment/webhook` - Webhook Paystack

### Produits
- `GET /api/products` - Liste des produits
- `GET /api/products/{id}` - Détail produit

### Codes d'accès
- `POST /api/access/verify` - Vérifier un code
- `POST /api/access/resend` - Renvoyer un code

### Portfolio
- `POST /api/portfolio/submit` - Soumettre un portfolio
- `POST /api/portfolio/pay/{id}` - Payer pour un portfolio
- `GET /api/portfolio/payment-status/{id}` - Statut du paiement
