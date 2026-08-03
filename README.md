# Arclith Sample

Implémentation fonctionnelle minimale d'Arclith pour tester le framework en conditions réelles.

Ce dépôt expose un CRUD `Ingredient` via FastAPI et FastMCP, avec adapters memory, MongoDB et DuckDB. Il sert de bac à sable pour valider les primitives du framework avant publication.

## Project Links

- Framework: [karned-rekipe/arclith](https://github.com/karned-rekipe/arclith)
- Sample repository: [karned-rekipe/_sample](https://github.com/karned-rekipe/_sample)
- GitHub Project: [Arclith backlog](https://github.com/orgs/karned-rekipe/projects/5)
- Framework issues: [Arclith issues](https://github.com/karned-rekipe/arclith/issues)

## Architecture

| Dossier | Rôle |
|---|---|
| `src/arclith_sample/domain/models/` | Entités et objets valeur du domaine métier, sans dépendance extérieure |
| `src/arclith_sample/domain/ports/` | Interfaces abstraites entre le domaine et le monde extérieur |
| `src/arclith_sample/application/use_cases/` | Cas d'usage applicatifs |
| `src/arclith_sample/application/services/` | Services applicatifs construits sur les use cases Arclith |
| `src/arclith_sample/adapters/input/` | Adaptateurs entrants FastAPI et FastMCP |
| `src/arclith_sample/adapters/output/` | Adaptateurs sortants memory, MongoDB, DuckDB |
| `src/arclith_sample/infrastructure/` | Câblage global, configuration et injection des dépendances |

---

## Lancement

### Prérequis

```bash
uv sync
```

### Configuration Keycloak (authentification JWT)

Le projet utilise Keycloak pour l'authentification JWT. Pour initialiser Keycloak avec le realm et le client
nécessaires :

```bash
# Depuis la racine du workspace local qui contient les scripts Keycloak
python scripts/seed_keycloak.py
```

Ce script crée automatiquement :

- **Realm** : `sample`
- **Client** : `sample` (configuré pour PKCE)
- **User de test** : `test` / `test`
- **Redirect URIs** : configurés pour Swagger UI sur le port 8000

Configuration attendue :

- Keycloak : `http://127.0.0.1:5990`
- Realm : `sample`
- Client ID : `sample`

Vous pouvez ensuite tester l'authentification depuis Swagger UI : http://127.0.0.1:8000/docs

### 1. API REST (FastAPI)

Expose un CRUD HTTP sur les ingrédients.

```bash
MODE=api uv run --frozen python main.py
```

- Swagger UI : [http://localhost:8000/docs](http://localhost:8000/docs)
- Base URL : `http://localhost:8000/ingredient/v1/`

### 2. Serveur MCP SSE

Expose les outils MCP via HTTP SSE. Le serveur doit tourner avant que le client s'y connecte.  
Tourne sur le port **8000**

```bash
MODE=mcp_sse uv run --frozen python main.py
```

- SSE endpoint : `http://localhost:8001/sse`
- Messages endpoint : `http://localhost:8001/messages/`

Configuration `mcp.json` :

```json
{
  "mcpServers": {
    "arclith-ingredients-sse": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

> **Note** : les serveurs MCP partagent la même instance FastMCP assemblée dans `main.py`. Ajouter un nouveau transport ne nécessite aucune modification du domaine.

---

## Passer de Memory à MongoDB

L'adapter actif est piloté par `config/adapters/adapters.yaml`.

```yaml
repository: mongodb
```

La configuration MongoDB se trouve dans `config/adapters/output/mongodb.yaml`. Le domaine, les services et les cas d'usage restent indépendants de MongoDB.
