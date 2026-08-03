# AGENTS.md — Arclith sample (`_sample/`)

## Contexte global

`_sample/` est le bac à sable R&D d'Arclith. Il sert à tester et faire évoluer `arclith` avant toute publication sur
PyPI. Il implémente un CRUD `Ingredient` minimal pour valider les primitives du framework. **Ne jamais déployer.**

## Rôle

- Valider les nouvelles fonctionnalités d'`arclith` en condition réelle avant merge/release
- Expérimenter de nouveaux patterns (transports MCP, adapters, multitenant…)
- Servir de référence d'implémentation minimale pour les nouveaux contributeurs

## Règles de développement

- Ce repo peut utiliser `arclith` en mode **editable** depuis `../arclith` (voir `pyproject.toml`)
- Toute modification doit rester expérimentale — aucune logique métier permanente
- Les tests sont indicatifs, pas une gate de qualité (contrairement à `recipe/` et `agent-recipe-creator/`)

## Architecture locale

```
src/arclith_sample/
  domain/
    models/ingredient.py      # Ingredient — entité de test minimale
    ports/ingredient_repository.py

  application/
    services/ingredient_service.py

  adapters/
    input/
      fastapi/
        routers/ingredient_router.py     # REST
        router.py                        # Register routers (point d'entrée)
      fastmcp/
        tools/ingredient_tools.py        # MCP tools
        tools.py                         # Register tools (point d'entrée)
        prompts/ingredient_prompts.py    # MCP prompts
        prompts.py                       # Register prompts (point d'entrée)
        resources/ingredient_resources.py # MCP resources
        resources.py                     # Register resources (point d'entrée)
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
MODE=api uv run --frozen python main.py      # REST :8000
MODE=mcp_sse uv run --frozen python main.py  # MCP SSE :8001
uv run --frozen pytest -v

# Utiliser Arclith local en editable
# Dans pyproject.toml :
# [tool.uv.sources]
# arclith = { path = "../arclith", editable = true }
uv sync
```

## Fichiers à lire en premier

1. `src/arclith_sample/infrastructure/containers/ingredient_container.py` — pattern de référence pour un container
2. `src/arclith_sample/adapters/input/fastmcp/tools/ingredient_tools.py` — pattern simplifié de registration MCP
3. `src/arclith_sample/adapters/input/fastapi/routers/ingredient_router.py` — pattern REST conforme HTTP conventions
4. `config/` — configuration minimale pour le dev local
5. `../arclith/docs/http-conventions.md` — conventions HTTP/REST SOTA
