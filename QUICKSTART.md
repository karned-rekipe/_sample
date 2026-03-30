# 🚀 Guide de démarrage rapide — _sample

Ce guide vous permet de démarrer rapidement le projet `_sample` avec authentification Keycloak.

## 📋 Prérequis

- Python 3.13
- Keycloak 26+ en cours d'exécution sur le port 5990
- `uv` (gestionnaire de packages)

## 🔧 Installation

```bash
cd /Users/killian/Karned/repos/Rekipe/_sample
uv sync --frozen
```

## 🔐 Configuration Keycloak

### 1. Vérifier que Keycloak est accessible

```bash
curl http://127.0.0.1:5990
```

Si Keycloak n'est pas démarré, lancez-le (via Docker, Podman, ou installation locale).

### 2. Initialiser le realm et le client

Depuis la **racine du workspace Rekipe** :

```bash
cd /Users/killian/Karned/projets/Rekipe
python scripts/seed_keycloak.py
```

Ce script crée :

- **Realm** : `sample`
- **Client ID** : `sample` (PKCE activé)
- **User de test** : `test` / `test`
- **Redirect URIs** : configurés pour Swagger UI

### 3. Vérifier la configuration

```bash
# Vérifier que le realm existe
curl http://127.0.0.1:5990/realms/sample/.well-known/openid-configuration | jq .issuer

# Doit retourner : "http://127.0.0.1:5990/realms/sample"
```

## 🚀 Lancer l'application

### Mode API (FastAPI REST)

```bash
cd /Users/killian/Karned/repos/Rekipe/_sample
MODE=api uv run --frozen python main.py
```

L'API démarre sur **http://127.0.0.1:8000**

### Mode MCP HTTP

```bash
cd /Users/killian/Karned/repos/Rekipe/_sample
MODE=mcp_http uv run --frozen python main.py
```

Le serveur MCP démarre sur **http://127.0.0.1:8001**

### Mode MCP SSE

```bash
cd /Users/killian/Karned/repos/Rekipe/_sample
MODE=mcp_sse uv run --frozen python main.py
```

### Mode ALL (API + MCP HTTP)

```bash
cd /Users/killian/Karned/repos/Rekipe/_sample
MODE=all uv run --frozen python main.py
```

Démarre simultanément :

- **API REST** : http://127.0.0.1:8000
- **MCP HTTP** : http://127.0.0.1:8001
- **Probes** : http://127.0.0.1:9000 (health, ready, metrics)

## 🧪 Tester l'authentification

### Via Swagger UI

1. Ouvrez http://127.0.0.1:8000/docs
2. Cliquez sur le bouton **Authorize** (🔒) en haut à droite
3. Laissez tous les champs par défaut et cliquez sur **Authorize**
4. Vous serez redirigé vers Keycloak
5. Connectez-vous avec :
    - **Username** : `test`
    - **Password** : `test`
6. Vous êtes maintenant authentifié !

### Via cURL (obtenir un token)

```bash
# Obtenir un token directement
curl -X POST "http://127.0.0.1:5990/realms/sample/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sample" \
  -d "username=test" \
  -d "password=test" \
  -d "grant_type=password" | jq -r .access_token
```

### Appeler l'API avec le token

```bash
# Obtenir le token
TOKEN=$(curl -s -X POST "http://127.0.0.1:5990/realms/sample/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sample" \
  -d "username=test" \
  -d "password=test" \
  -d "grant_type=password" | jq -r .access_token)

# Appeler l'API
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/ingredient/v1/
```

## 🔍 Endpoints utiles

| Endpoint                             | Description           |
|--------------------------------------|-----------------------|
| http://127.0.0.1:8000/docs           | Swagger UI (API REST) |
| http://127.0.0.1:8000/ingredient/v1/ | CRUD Ingredient       |
| http://127.0.0.1:9000/health         | Health check          |
| http://127.0.0.1:9000/ready          | Readiness probe       |
| http://127.0.0.1:9000/info           | Application info      |
| http://127.0.0.1:9000/metrics        | Prometheus metrics    |

## ❌ Dépannage

### Erreur "Realm does not exist"

→ Le realm `sample` n'a pas été créé dans Keycloak. Exécutez `python scripts/seed_keycloak.py`

### Erreur "page not found" sur Keycloak

→ Vérifiez que :

- La configuration dans `config/adapters/input/keycloak.yaml` correspond à votre Keycloak
- Le `redirect_uri` pointe vers le bon port (8000 par défaut)

### Swagger UI : erreur d'autorisation

→ Vérifiez que :

- Le client `sample` existe dans Keycloak
- Les `redirect_uris` incluent `http://127.0.0.1:8000/docs/oauth2-redirect`
- PKCE est activé sur le client

### Port 8000 déjà utilisé

→ Changez le port dans `config/adapters/input/fastapi.yaml` et relancez `seed_keycloak.py` avec le nouveau port

## 📚 Documentation

- Architecture : `AGENTS.md`
- Configuration complète : `config/`
- Décisions : `framework/docs/decisions.md`
- Auth JWT : `framework/docs/auth.md`

