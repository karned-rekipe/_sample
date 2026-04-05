# Configurer Vault et les secrets

`arclith` injecte des secrets dans la config au démarrage via un système de **mappings**.
Chaque mapping associe un champ de config (chemin pointé) à une clé dans le resolver actif (Vault, YAML ou env).

```
config.yaml  secrets.mappings
      ↓               ↓
adapters.lm.api_key → rekipe/sample/lm  →  Vault kv/rekipe/sample/lm → value = "sk-ant-..."
                                                       ↑
                                              VAULT_TOKEN (env ou ~/.vault-token)
```

---

## Démarrer Vault en dev local

```bash
# Démarrer Vault (Docker, mode dev — données non persistées)
docker run --rm -d \
  --name vault-dev \
  -p 5991:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-token \
  hashicorp/vault

# Exporter les variables d'environnement
export VAULT_ADDR=http://127.0.0.1:5991
export VAULT_TOKEN=dev-token

# Vérifier la connexion
vault status

# Activer le mount KV v2 (déjà actif en mode dev sous "secret/", en créer un dédié)
vault secrets enable -path=kv -version=2 kv
```

> En mode dev Vault crée automatiquement un mount `secret/`. Le projet utilise `kv/` — activer le mount ci-dessus si c'est la première fois.

---

## Secrets statiques (injectés au démarrage)

La section `secrets` dans `config/secrets.yaml` (ou `config.yaml`) contrôle quel resolver utiliser et quels champs injecter :

```yaml
# config/secrets.yaml
resolver: vault          # vault | yaml | env | chain
mappings:
  adapters.mongodb.uri:  rekipe/sample/mongodb   # champ config → chemin Vault
  adapters.lm.api_key:   rekipe/sample/lm        # ← ajouter pour résoudre l'erreur api_key

vault:
  addr: http://127.0.0.1:5991   # overridable via VAULT_ADDR
  mount: kv
```

> `VAULT_ADDR` (variable d'env) prend toujours la priorité sur `vault.addr` dans le YAML — utile en CI/prod.

### Adapter MongoDB — URI

```bash
vault kv put kv/rekipe/sample/mongodb \
  value="mongodb://user:pass@localhost:27017"
```

```yaml
# config/secrets.yaml — mappings
adapters.mongodb.uri: rekipe/sample/mongodb
```

### Adapter LM — api_key

C'est la cause de `RuntimeError: api_key is not set`.

```bash
# Anthropic
vault kv put kv/rekipe/sample/lm \
  value="sk-ant-..."

# OpenAI
vault kv put kv/rekipe/sample/lm \
  value="sk-..."
```

```yaml
# config/secrets.yaml — mappings
adapters.lm.api_key: rekipe/sample/lm
```

### Cache Redis — redis_url (optionnel)

En dev, Redis n'a généralement pas d'authentification — laisser `redis_url` dans la config suffit.
Si Redis exige un mot de passe en production :

```bash
vault kv put kv/rekipe/sample/redis \
  value="redis://user:pass@redis:6379"
```

```yaml
# config/secrets.yaml — mappings
cache.redis_url: rekipe/sample/redis
```

---

## Chain resolver — fallback yaml en dev

Le resolver `chain` essaie chaque source dans l'ordre et retourne la première valeur non nulle.
Pattern recommandé : Vault en priorité, fallback sur `secrets.yaml` local si Vault est injoignable.

```yaml
# config/secrets.yaml
resolver: chain
chain: [vault, yaml]    # essaie Vault d'abord, puis secrets.yaml
mappings:
  adapters.mongodb.uri: rekipe/sample/mongodb
  adapters.lm.api_key:  rekipe/sample/lm

vault:
  addr: http://127.0.0.1:5991
  mount: kv

yaml:
  path: secrets.yaml    # fallback local — gitignored
```

```yaml
# secrets.yaml (fallback local, gitignored)
adapters:
  mongodb:
    uri: mongodb://localhost:27017
  lm:
    api_key: sk-ant-...
```

| Resolver | Usage | Auth |
|----------|-------|------|
| `vault`  | Production, CI | `VAULT_TOKEN` ou `~/.vault-token` |
| `yaml`   | Dev local       | Aucune — fichier gitignored |
| `env`    | CI, containers  | Variables d'environnement |
| `chain`  | Dev → prod sans changer le code | Selon les resolvers de la chaîne |

---

## Multi-tenant MongoDB (avancé)

En mode `multitenant: true`, les credentials MongoDB ne sont plus statiques — ils sont résolus **par requête** depuis Vault selon le `tenant_id` extrait du JWT.

### 1. Stocker les credentials par tenant dans Vault

```bash
# Un secret par tenant — toutes les clés sont libres
vault kv put kv/rekipe/tenants/client-a \
  uri="mongodb://user:pass@mongo-a:27017" \
  db_name="client_a"

vault kv put kv/rekipe/tenants/client-b \
  uri="mongodb://user:pass@mongo-b:27017" \
  db_name="client_b"
```

### 2. Configurer `config.yaml`

```yaml
adapters:
  repository: mongodb
  mongodb:
    multitenant: true
    db_name: fallback_db   # utilisé si Vault ne retourne pas de db_name

tenant:
  vault_addr: http://127.0.0.1:5991
  vault_mount: kv
  vault_path_prefix: rekipe/tenants   # → rekipe/tenants/{tenant_id}
  tenant_claim: sub                   # claim JWT qui porte le tenant_id

cache:
  backend: redis          # redis recommandé en prod pour partager le cache entre workers
  redis_url: redis://127.0.0.1:6379
  tenant_uri_ttl: 300     # secondes — vider ce cache après migration de base
```

### 3. Câbler `VaultTenantResolver` dans le container

```python
# infrastructure/containers/ingredient_container.py
from arclith.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from arclith.adapters.input.jwt.decoder import JWTDecoder
from arclith.adapters.input.license.validator import RoleLicenseValidator
from arclith.adapters.output.vault.tenant_adapter import VaultTenantResolver

def build_inject_tenant(arclith: Arclith):
    cfg = arclith.config
    cache = arclith._cache

    return make_inject_tenant_uri(
        cfg,
        jwt_decoder=JWTDecoder(
            jwks_uri=f"{cfg.keycloak.url}/realms/{cfg.keycloak.realm}/protocol/openid-connect/certs",
            audience=cfg.keycloak.audience,
            cache=cache,
            ttl_s=cfg.cache.jwks_ttl,
        ),
        license_validator=RoleLicenseValidator(role=cfg.license.role),
        tenant_resolvers=[
            VaultTenantResolver(
                "mongodb",
                addr=cfg.tenant.vault_addr,
                mount=cfg.tenant.vault_mount,
                path_prefix=cfg.tenant.vault_path_prefix,
                cache=cache,
                ttl_s=cfg.cache.tenant_uri_ttl,
            ),
        ],
    )
```

```python
# adapters/input/fastapi/routers/ingredient_router.py
router = APIRouter(dependencies=[Depends(inject_tenant)])
```

Le repository MongoDB lit ensuite les coords injectées dans le `ContextVar` :

```python
# Dans MongoDBIngredientRepository (ou MongoDBRepository de base)
from arclith.adapters.context import get_adapter_tenant_context

coords = get_adapter_tenant_context("mongodb")
uri     = coords.get("uri")     or self._config.uri
db_name = coords.get("db_name") or self._config.db_name
```

---

## Résumé — quels adapters utilisent Vault

| Adapter | Secret | Chemin Vault (exemple) | Mode |
|---------|--------|------------------------|------|
| MongoDB | `adapters.mongodb.uri` | `kv/rekipe/sample/mongodb` | Statique (démarrage) |
| LM | `adapters.lm.api_key` | `kv/rekipe/sample/lm` | Statique (démarrage) |
| Redis | `cache.redis_url` | `kv/rekipe/sample/redis` | Statique, optionnel |
| MongoDB multi-tenant | `uri` + `db_name` par tenant | `kv/rekipe/tenants/{tenant_id}` | Par requête |
| DuckDB | — | — | Fichier local, pas de secret |
| Memory | — | — | Pas de secret |

