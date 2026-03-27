# HTTP Conventions — REST & MCP

## Status Codes (SOTA)

Tous les endpoints FastAPI DOIVENT déclarer explicitement leur `status_code` et `responses` si applicable.

### POST — Create

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `POST /v1/resources` | **201 Created** | `{ uuid, ...metadata }` | Succès création |
| | **400 Bad Request** | `{ detail }` | Validation payload échouée |
| | **409 Conflict** | `{ detail }` | Conflit (ex. doublon contrainte unique) |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur inattendue |

**Convention :** retourner 201 + body minimal avec UUID de la ressource créée.  
Exposer `Location` header si pertinent (optionnel dans notre stack).

### GET — Read

#### GET Single Resource

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `GET /v1/resources/{uuid}` | **200 OK** | `{ uuid, fields... }` | Ressource trouvée |
| | **404 Not Found** | `{ detail }` | Ressource inexistante ou soft-deleted |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** retourner 200 + body complet. 404 si non trouvée.

#### GET List

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `GET /v1/resources` | **200 OK** | `[]` ou `[{ uuid, ... }]` | Liste vide = 200 OK avec `[]` |
| | **400 Bad Request** | `{ detail }` | Paramètres query invalides |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** toujours 200 OK même si liste vide. Pas de 404 pour liste vide.

### PUT — Replace

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `PUT /v1/resources/{uuid}` | **204 No Content** | ∅ | Succès remplacement complet |
| | **404 Not Found** | `{ detail }` | Ressource inexistante |
| | **400 Bad Request** | `{ detail }` | Payload invalide |
| | **409 Conflict** | `{ detail }` | Optimistic lock failure (version mismatch) |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** 204 + body vide. Client doit re-fetch avec GET s'il veut l'état final.

### PATCH — Partial Update

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `PATCH /v1/resources/{uuid}` | **204 No Content** | ∅ | Succès mise à jour partielle |
| | **404 Not Found** | `{ detail }` | Ressource inexistante |
| | **400 Bad Request** | `{ detail }` | Payload invalide |
| | **409 Conflict** | `{ detail }` | Optimistic lock failure |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** identique à PUT — 204 + body vide.

### DELETE — Soft Delete

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `DELETE /v1/resources/{uuid}` | **204 No Content** | ∅ | Succès soft-delete |
| | **404 Not Found** | `{ detail }` | Ressource déjà supprimée ou inexistante |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** 204 + body vide. Idempotent — DELETE sur ressource déjà deleted = 204 (pas 404).

### DELETE — Purge (batch)

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `DELETE /v1/resources/purge` | **200 OK** | `{ purged: <count> }` | Succès suppression physique |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** 200 + body JSON avec compteur. Jamais 204 car on retourne une métrique.

### POST — Actions / Special Endpoints

| Endpoint | Status | Response Body | Cas |
|---|---|---|---|
| `POST /v1/resources/{uuid}/duplicate` | **201 Created** | `{ uuid }` | Succès duplication |
| | **404 Not Found** | `{ detail }` | Ressource source inexistante |
| | **500 Internal Server Error** | `{ detail }` | Erreur serveur |

**Convention :** 201 si création d'une nouvelle ressource. 200 si action ne créant pas de ressource.

---

## Déclaration dans FastAPI

### ✅ Bon — Déclaration explicite

```python
self.router.add_api_route(
    methods=["POST"],
    path="/",
    endpoint=self.create_resource,
    summary="Create resource",
    response_model=ResourceCreatedSchema,
    status_code=201,  # ✅ Explicite
    responses={
        400: {"description": "Invalid payload"},
        409: {"description": "Resource already exists"},
    },
)
```

### ❌ Mauvais — Status code implicite

```python
self.router.add_api_route(
    methods=["POST"],
    path="/",
    endpoint=self.create_resource,
    # ❌ Pas de status_code — FastAPI défaut = 200
)
```

---

## MCP Tools — Retours

Les MCP tools ne retournent **pas** de status codes HTTP — ils retournent des objets JSON ou `None`.

### Convention MCP

| Opération | Retour | Erreur |
|---|---|---|
| Create | `dict` (objet complet) | Exception levée |
| Read | `dict \| None` | `None` si non trouvé (pas d'exception) |
| Update | `dict` (objet mis à jour) ou `None` | Exception si non trouvé |
| Delete | `None` ou `{ deleted: true }` | Exception si non trouvé |
| List | `list[dict]` | Toujours `[]` si vide, jamais `None` |

**Règle :** les MCP tools **ne lèvent pas** HTTPException. Ils retournent `None` ou une liste vide. Les erreurs métier génèrent des exceptions Python classiques (ValueError, RuntimeError).

---

## Résumé SOTA

| Verbe | Action | Status Success | Body Success | Status Error |
|---|---|---|---|---|
| POST | Create | 201 | `{ uuid, ... }` | 400, 409, 500 |
| POST | Duplicate | 201 | `{ uuid }` | 404, 500 |
| GET | Read One | 200 | `{ uuid, ... }` | 404, 500 |
| GET | List | 200 | `[]` ou `[...]` | 400, 500 |
| PUT | Replace | 204 | ∅ | 400, 404, 409, 500 |
| PATCH | Partial | 204 | ∅ | 400, 404, 409, 500 |
| DELETE | Soft | 204 | ∅ | 404, 500 |
| DELETE | Purge | 200 | `{ purged: N }` | 500 |

---

## Principes

1. **Explicite > Implicite** : toujours déclarer `status_code` dans `add_api_route`.
2. **204 = No Content** : PUT/PATCH/DELETE ne retournent rien en cas de succès.
3. **201 = Created** : POST qui crée une ressource retourne 201 + UUID.
4. **200 = OK** : GET (list ou single) + actions retournant un body.
5. **404 = Not Found** : déclarer dans `responses={}` pour tout endpoint avec `{uuid}` path param.
6. **Liste vide ≠ 404** : `GET /v1/resources` retourne toujours 200 OK, même si `[]`.
7. **MCP tools ≠ HTTP** : pas de status codes, retour `None` ou `dict` direct.

---

## Références

- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [REST API Design Rulebook (O'Reilly)](https://www.oreilly.com/library/view/rest-api-design/9781449317904/)
- [FastAPI Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/)

