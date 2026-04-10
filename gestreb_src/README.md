# GESTREB — Backend FastAPI

Conversion complète du backend **Node.js / Express** vers **Python / FastAPI**,  
avec conservation intégrale du frontend (templates EJS → Jinja2, CSS, JS, libs).

---

## Structure du projet

```
gestreb_fastapi/
├── server.py              # Point d'entrée FastAPI (équivalent server.js)
├── database.py            # Pool asyncpg (équivalent new Client pg)
├── auth.py                # JWT cookie httpOnly (équivalent jsonwebtoken)
├── email_utils.py         # Envoi SMTP (équivalent nodemailer)
├── requirements.txt
├── .env.example
│
├── routes/
│   ├── auth.py            # /connexion, /inscription, /valid, /rejet, /validation, /log/deconnecter
│   ├── pages.py           # Toutes les routes res.render() → TemplateResponse
│   ├── parcelles.py       # /api/parcelles, /get/parcelles/*, /api/donnees, /mise_en_place, ...
│   ├── missions.py        # /api/agents, /mission, /api/planifier_mission, /api/valider_mission,
│   │                      #   /inventaire, /api/dossier_ivt, /api/valider_ivt
│   └── dashboard.py       # /dashboard/00000/:id, /requete/:id, /elements/*, /iteration
│
├── templates/             # 49 templates EJS convertis en Jinja2 (syntaxe <%= %> → {{ }})
│   ├── connexion.html
│   ├── inscription.html
│   ├── dashboard_conn.html
│   └── ...
│
└── static/                # Copie exacte du dossier public/ Node.js
    ├── css/
    ├── js/
    ├── img/
    ├── json/              # Fichiers GeoJSON (mis à jour dynamiquement)
    └── libs/              # Bootstrap, OpenLayers, jQuery, ol-layerswitcher...
```

---

## Correspondances Node.js → FastAPI

| Concept Node.js/Express     | Équivalent FastAPI/Python        |
|-----------------------------|----------------------------------|
| `express` + `app.get/post`  | `FastAPI` + `@router.get/post`   |
| `res.render('vue', data)`   | `templates.TemplateResponse()`   |
| `res.json(data)`            | `return [dict(r) for r in rows]` |
| `res.redirect('/url')`      | `RedirectResponse('/url')`       |
| `pg.Client` (callbacks)     | `asyncpg` pool (async/await)     |
| `jsonwebtoken`              | `PyJWT`                          |
| `bcrypt` (Node)             | `bcrypt` (Python)                |
| `nodemailer`                | `smtplib` (stdlib Python)        |
| `express-session` + `flash` | `starlette SessionMiddleware`    |
| `express.static('public')`  | `StaticFiles(directory='static')`|
| `ejs` templates             | `Jinja2Templates`                |
| `dotenv`                    | `python-dotenv`                  |
| `random-token`              | `secrets.token_hex()`            |
| `connect-ensure-login`      | `require_auth()` custom          |
| `fs.writeFile`              | `open(..., 'w')` Python          |
| `Buffer.from(b64, 'base64')`| `base64.b64decode()`             |

---

## Installation et démarrage

### 1. Prérequis

- Python 3.11+
- PostgreSQL accessible (Render, local, etc.)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Éditer .env avec vos vraies valeurs
```

### 4. Démarrage

```bash
# Développement
uvicorn server:app --host 0.0.0.0 --port 3004 --reload

# Production
uvicorn server:app --host 0.0.0.0 --port 3004 --workers 4
```

L'application sera disponible sur : http://localhost:3004

### Documentation API automatique

- Swagger UI : http://localhost:3004/docs
- ReDoc : http://localhost:3004/redoc

---

## Conversion des templates EJS → Jinja2

Les 49 templates `.ejs` ont été convertis automatiquement vers Jinja2 :

| EJS                          | Jinja2                    |
|------------------------------|---------------------------|
| `<%= variable %>`            | `{{ variable }}`          |
| `<%- html %>`                | `{{ html \| safe }}`      |
| `<% if (cond) { %>`          | `{% if cond %}`           |
| `<% } else { %>`             | `{% else %}`              |
| `<% } %>`                    | `{% endif %}`             |
| `arr.forEach(x => { %>`      | `{% for x in arr %}`      |
| `new Date().getFullYear()`   | `current_year`            |
| `x && y` (dans `{% %}`)      | `x and y`                 |
| `x \|\| y` (dans `{% %}`)    | `x or y`                  |
| `arr.length > 0`             | `arr` (truthy check)      |

---

## Notes importantes

### Sécurité améliorée vs Node.js original
- Les opérateurs SQL dans `/requete/:id` sont validés via **whitelist** (protection injection SQL)
- Tous les paramètres DB utilisent `$1, $2...` (requêtes paramétrées asyncpg)
- Le `SECRET_KEY` JWT doit être changé en production

### Différences comportementales
- Les `setTimeout()` Express (workaround callbacks) sont supprimés — remplacés par `async/await` propre
- Le pool asyncpg remplace le client `pg` unique partagé (meilleure gestion concurrence)
- Les credentials SMTP sont en variables d'environnement (vs hardcodés dans le JS)

### Variables de session (flash messages)
Les messages flash `req.flash()` sont remplacés par `request.session["error"]` / `request.session["success"]`.
Ils sont lus et effacés dans les templates via `.pop()`.

---

## Déploiement sur Render

Le projet est compatible avec Render (même hébergeur que la DB).

**Build command :**
```
pip install -r requirements.txt
```

**Start command :**
```
uvicorn server:app --host 0.0.0.0 --port $PORT
```
