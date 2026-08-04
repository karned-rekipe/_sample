# Quickstart demo Arclith sample

Ce guide lance `_sample` comme banc de test concret pour les evolutions Arclith. Le parcours par defaut utilise l'adapter `memory`, sans MongoDB ni Keycloak, afin de valider vite le coeur hexagonal, l'API, MCP et les probes.

## Objectif

`_sample` doit rester l'implementation fonctionnelle de reference:

- un domaine `Ingredient` independant des frameworks;
- un port repository et plusieurs adapters outbound (`memory`, `mongodb`, `duckdb`);
- des adapters inbound FastAPI et FastMCP qui exposent les memes cas d'usage;
- des probes `health`, `ready`, `info` et `metrics`;
- un smoke test executable localement et en CI.

## Prerequis

- Python 3.13
- `uv`
- `curl`

## 1. Installer

```bash
git clone https://github.com/karned-rekipe/_sample.git
cd _sample
if [ -f uv.lock ]; then uv sync --frozen; else uv sync; fi
```

Le clone `_sample` utilise `uv.lock` avec `--frozen`.
Un projet genere par `arclith-cli` n'a pas encore de lockfile; le premier `uv sync` le cree.

## 2. Lancer le sample

Le mode `all` lance l'API FastAPI, MCP HTTP et les probes.

```bash
MODE=all uv run --frozen python main.py
```

Endpoints par defaut:

- API REST: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- MCP HTTP: `http://127.0.0.1:8001/mcp`
- probes: `http://127.0.0.1:9000`

Si le port `8001` est deja occupe localement, utiliser `MODE=api` pour valider l'API et les probes avec `make demo-smoke`. Pour valider MCP, liberer `8001` ou ajuster `config/adapters/inbound/fastmcp.yaml`.

## 3. Verifier le runtime

Dans un deuxieme terminal:

```bash
curl -fsS http://127.0.0.1:9000/health
curl -fsS http://127.0.0.1:9000/ready
curl -fsS http://127.0.0.1:9000/info
curl -fsS http://127.0.0.1:9000/metrics
```

## 4. Jouer la demo CRUD

Le smoke test cree un ingredient, le relit, filtre la liste et teste la duplication.

```bash
make demo-smoke
```

Le script accepte des URL custom si les ports changent:

```bash
API_BASE=http://127.0.0.1:8100 PROBE_BASE=http://127.0.0.1:9100 make demo-smoke
```

## 5. Tester manuellement l'API

```bash
CREATE_RESPONSE=$(curl -fsS -X POST http://127.0.0.1:8000/v1/ingredients/ \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-$(uv run --frozen python -c 'import uuid; print(uuid.uuid4())')" \
  -H "Prefer: return=representation" \
  -d '{"name":"Farine demo Arclith"}')

echo "$CREATE_RESPONSE"

INGREDIENT_ID=$(CREATE_RESPONSE="$CREATE_RESPONSE" uv run --frozen python - <<'PY'
import json
import os

print(json.loads(os.environ["CREATE_RESPONSE"])["data"]["uuid"])
PY
)

curl -fsS "http://127.0.0.1:8000/v1/ingredients/$INGREDIENT_ID"
curl -fsS "http://127.0.0.1:8000/v1/ingredients/?name=Farine"
curl -fsS -X POST "http://127.0.0.1:8000/v1/ingredients/$INGREDIENT_ID/duplicate" \
  -H "Prefer: return=representation"
```

## 6. Changer l'adapter repository

L'adapter actif est pilote par:

```text
config/adapters/adapters.yaml
```

Valeur par defaut:

```yaml
repository: memory
```

### DuckDB

1. Mettre `repository: duckdb` dans `config/adapters/adapters.yaml`.
2. Verifier `config/adapters/outbound/duckdb.yaml`.
3. Relancer `MODE=all uv run --frozen python main.py`.
4. Rejouer `make demo-smoke`.

### MongoDB

1. Mettre `repository: mongodb` dans `config/adapters/adapters.yaml`.
2. Verifier `config/adapters/outbound/mongodb.yaml`.
3. Garder l'URI MongoDB dans `secrets.yaml`, une variable d'environnement ou Vault. Ne jamais commiter l'URI.
4. Relancer `MODE=all uv run --frozen python main.py`.
5. Rejouer `make demo-smoke`.

## 7. Auth Keycloak

Keycloak n'est pas requis pour le smoke test de base. Il devient utile pour valider les endpoints proteges comme `DELETE /v1/ingredients/{uuid}` et les routes admin.

Configuration attendue:

- Keycloak: `http://127.0.0.1:5990`
- Realm: `sample`
- Client ID: `sample`
- User de test: `test` / `test`

Si les scripts Keycloak sont disponibles dans ton workspace:

```bash
python scripts/seed_keycloak.py
```

Puis tester l'authentification via Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## 8. Valider une evolution Arclith

Avant de publier une evolution du framework:

```bash
make quality
```

Terminal 1:

```bash
MODE=all uv run --frozen python main.py
```

Terminal 2:

```bash
make demo-smoke
```

La regle de fond: si Arclith change, `_sample` doit continuer a demontrer que le domaine reste independant des adapters et que les transports API/MCP appellent les memes cas d'usage.
