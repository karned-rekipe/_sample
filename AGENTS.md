# AGENTS.md — `_sample/`

## Contexte global

`_sample/` est le bac à sable R&D de Rekipe. Il sert à tester et faire évoluer `arclith` avant toute publication sur
PyPI. Il implémente un CRUD `Ingredient` minimal pour valider les primitives du framework. **Ne jamais déployer.**

## Rôle

- Valider les nouvelles fonctionnalités d'`arclith` en condition réelle avant merge/release
- Expérimenter de nouveaux patterns (transports MCP, adapters, multitenant…)
- Servir de référence d'implémentation minimale pour les nouveaux contributeurs

## Règles de développement

- Ce repo utilise `arclith` en mode **editable** depuis `../framework` (voir `pyproject.toml`)
- Toute modification doit rester expérimentale — aucune logique métier permanente
- Les tests sont indicatifs, pas une gate de qualité (contrairement à `recipe/` et `agent-recipe-creator/`)

## Architecture locale

```
domain/
  models/ingredient.py      # Ingredient — entité de test minimale
  ports/ingredient_repository.py

application/
  services/ingredient_service.py

adapters/
  input/
    fastapi/*_router.py     # REST
    fastmcp/*_tools.py      # MCP
  output/
    mongodb/repository.py
    duckdb/repository.py
    memory/repository.py

infrastructure/
  ingredient_container.py   # Pattern de référence pour les containers
```

## Configuration

```yaml
adapters:
  repository: memory   # memory | mongodb | duckdb
api:
  port: 8000
mcp:
  port: 8001
```

## Commandes utiles

```bash
uv run --frozen python main_api.py         # REST :8000
uv run --frozen python main_mcp_sse.py     # MCP SSE :8001
uv run --frozen pytest -v

# Utiliser le framework local en editable
# Dans pyproject.toml :
# [tool.uv.sources]
# arclith = { path = "../framework", editable = true }
uv sync
```

## Fichiers à lire en premier

1. `infrastructure/ingredient_container.py` — pattern de référence pour un container (alternative à `recipe/`)
2. `adapters/input/fastmcp/*_tools.py` — pattern simplifié de registration MCP
3. `config.yaml` — configuration minimale pour le dev local

