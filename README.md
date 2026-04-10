# NumStore - Boutique de Produits Numériques

Application FastAPI restructurée avec PostgreSQL et templates Jinja2.

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
│   ├── payments.py     # API paiements (Stripe)
│   ├── access.py       # API codes d'accès
│   ├── portfolio.py    # API portfolios
│   └── admin.py        # API admin
├── templates/          # Templates Jinja2
│   ├── base.html
│   ├── home.html
│   ├── product.html
│   ├── access.html
│   ├── portfolio_form.html
│   ├── portfolio_success.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_products.html
│   ├── admin_portfolios.html
│   └── 404.html
├── static/
│   └── css/
│       └── styles.css
├── requirements.txt
├── schema.sql          # Schema PostgreSQL
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
5. Notez les informations de connexion (Internal Database URL)

#### Étape 2: Initialiser le schema
1. Connectez-vous à la base de données avec un client PostgreSQL
2. Exécutez le contenu de `schema.sql`

#### Étape 3: Créer le Web Service
1. Dashboard Render → New → Web Service
2. Connectez votre repository
3. Configurez:
   - **Name**: numstore
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

#### Étape 4: Variables d'environnement
Ajoutez ces variables dans les settings du Web Service:

```
DB_HOST=<host from postgres>
DB_NAME=<dbname from postgres>
DB_PORT=5432
DB_PWD=<password from postgres>
DB_USER=<user from postgres>
SECRET_KEY=<générez une clé secrète>
ADMIN_PASSWORD=<mot de passe admin>
STRIPE_API_KEY=<votre clé Stripe>
RESEND_API_KEY=<votre clé Resend>
SENDER_EMAIL=onboarding@resend.dev
```

## Commandes de Build et Start

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

## Initialisation des données

Après le premier déploiement, appelez l'endpoint pour créer les produits initiaux:
```bash
curl -X POST https://votre-app.onrender.com/api/products/seed
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
- **Paiement** : Intégration Stripe
- **Codes d'accès** : Système de codes temporaires pour téléchargement
- **Portfolio** : Formulaire de création de portfolio avec workflow de validation
- **Admin** : Dashboard de gestion des produits et soumissions
- **Emails** : Notifications automatiques via Resend
