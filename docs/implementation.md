# Implémenter une entité avec arclith

Ce dossier est le projet de référence. Il montre comment brancher `arclith` pour une entité concrète : **Ingredient**.

Chaque section correspond à un fichier à créer, dans l'ordre des couches (de l'intérieur vers l'extérieur).

---

## 1. `src/arclith_sample/domain/models/` — L'entité

Hérite de `Entity`. Contient uniquement les champs métier et leur validation.

```python
# src/arclith_sample/domain/models/ingredient.py
from dataclasses import dataclass
from arclith.domain.models.entity import Entity


@dataclass
class Ingredient(Entity):
    name: str = ""
    unit: str | None = None

    def __post_init__(self) -> None:
        # validation métier ici
        if not self.name.strip():
            raise ValueError("Ingredient name cannot be empty")
```

> `Entity` apporte automatiquement : `uuid`, `created_at`, `updated_at`, `deleted_at`, `is_deleted`, `version`.

---

## 2. `src/arclith_sample/domain/ports/` — Le port spécifique

Si ton entité a des requêtes au-delà du CRUD générique, déclare-les ici sous forme d'interface abstraite.

```python
# src/arclith_sample/domain/ports/output/ingredient_repository.py
from abc import abstractmethod
from arclith.domain.ports.repository import Repository
from arclith_sample.domain.models.ingredient import Ingredient


class IngredientRepository(Repository[Ingredient]):
    @abstractmethod
    async def find_by_name(self, name: str) -> list[Ingredient]: ...
```

> Si ton entité n'a pas de requêtes spécifiques, utilise directement `Repository[T]` — pas besoin de ce fichier.

---

## 3. `src/arclith_sample/application/use_cases/` — Les cas d'usage spécifiques

Les use cases génériques (create, read, update…) sont fournis par `arclith`.  
Ajoute ici uniquement ce qui est propre à ton entité.

```python
# src/arclith_sample/application/use_cases/find_by_name.py
from arclith.domain.ports.logger import Logger
from arclith_sample.domain.models.ingredient import Ingredient
from arclith_sample.domain.ports.output.ingredient_repository import IngredientRepository


class FindByNameUseCase:
    def __init__(self, repository: IngredientRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def execute(self, name: str) -> list[Ingredient]:
        self._logger.info("🔍 Finding ingredients by name", name=name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ Ingredients found", name=name, count=len(result))
        return result
```

---

## 4. `src/arclith_sample/application/services/` — La façade de service

Étend `BaseService` pour exposer les méthodes aux adapters. Ne contient pas de logique — délègue aux use cases.

```python
# src/arclith_sample/application/services/ingredient_service.py
from arclith.application.services.base_service import BaseService
from arclith.domain.ports.logger import Logger
from arclith_sample.domain.models.ingredient import Ingredient
from arclith_sample.domain.ports.output.ingredient_repository import IngredientRepository
from arclith_sample.application.use_cases import FindByNameUseCase


class IngredientService(BaseService[Ingredient]):
    def __init__(self, repository: IngredientRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._find_by_name_uc = FindByNameUseCase(repository, logger)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return await self._find_by_name_uc.execute(name)
```

> `BaseService` expose déjà : `create`, `read`, `update`, `delete`, `find_all`, `duplicate`, `purge`.

---

## 5. `src/arclith_sample/adapters/input/schemas/` — Les schémas Pydantic

Séparent le modèle HTTP du modèle domaine. Un schéma par intention (création, mise à jour, réponse).

```python
# src/arclith_sample/adapters/input/schemas/ingredient_schema.py
from arclith.adapters.input.schemas.base_schema import BaseSchema


class IngredientCreateSchema(BaseModel):
    name: str
    unit: str | None = None


class IngredientSchema(BaseSchema):  # réponse — hérite de BaseSchema (uuid, timestamps…)
    name: str
    unit: str | None = None
```

> `BaseSchema` inclut automatiquement les champs de `Entity` dans la réponse.

---

## 6. `src/arclith_sample/adapters/output/` — Les repositories concrets

Implémente le port en héritant du repository `arclith` correspondant **et** du port spécifique.

```python
# src/arclith_sample/adapters/output/memory/repositories/ingredient_repository.py
from arclith.adapters.output.memory.repository import InMemoryRepository
from arclith_sample.domain.models.ingredient import Ingredient
from arclith_sample.domain.ports.output.ingredient_repository import IngredientRepository


class InMemoryIngredientRepository(InMemoryRepository[Ingredient], IngredientRepository):
    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [i for i in self._store.values() if name.lower() in i.name.lower()]
```

Même pattern pour MongoDB :

```python
# src/arclith_sample/adapters/output/mongodb/repositories/ingredient_repository.py
from arclith.adapters.output.mongodb.repository import MongoDBRepository


class MongoDBIngredientRepository(MongoDBRepository[Ingredient], IngredientRepository):
    def __init__(self, config: MongoDBConfig, logger: Logger) -> None:
        super().__init__(config, Ingredient, logger)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [self._from_doc(doc) async for doc in self._collection.find({"name": {"$regex": name, "$options": "i"}})]
```

---

## 7. `src/arclith_sample/infrastructure/containers/ingredient_container.py` — L'injection de dépendances

Lit la config via l'instance `Arclith` et instancie les dépendances. C'est le seul endroit où tout se branche.

```python
from arclith import Arclith, MongoDBConfig
from arclith_sample.domain.ports.output.ingredient_repository import IngredientRepository
from arclith_sample.application.services.ingredient_service import IngredientService


def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, ...]:
    logger = arclith.logger
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from arclith_sample.adapters.output.mongodb.repository import MongoDBIngredientRepository
            mongo = config.adapters.mongodb
            repo: IngredientRepository = MongoDBIngredientRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name),
                logger,
            )
        case "duckdb":
            from arclith_sample.adapters.output.duckdb.repository import DuckDBIngredientRepository
            repo = DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            from arclith_sample.adapters.output.memory.repository import InMemoryIngredientRepository
            repo = InMemoryIngredientRepository()
    return IngredientService(repo, logger, config.soft_delete.retention_days), logger
```

---

## 8. `src/arclith_sample/adapters/input/fastapi/dependencies.py` — Multitenancy FastAPI

Crée le `inject_tenant_uri` qui sera injecté sur toutes les routes.

```python
from pathlib import Path
from arclith.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from arclith.infrastructure.config import load_config_dir

inject_tenant_uri = make_inject_tenant_uri(
    load_config_dir(Path(__file__).resolve().parents[5] / "config")
)
```

Puis dans le router :

```python
from fastapi import APIRouter, Depends
from arclith_sample.adapters.input.fastapi.dependencies import inject_tenant_uri

self.router = APIRouter(
    prefix="/ingredient/v1",
    tags=["ingredients"],
    dependencies=[Depends(inject_tenant_uri)],
)
```

---

## 9. `config.yaml` — La configuration

Choisit le repository actif, configure les connexions et le mode multitenancy.

```yaml
adapters:
  repository: memory    # memory | mongodb | duckdb
  multitenant: false    # true = URI résolue par requête (vault via JWT)

  mongodb:
    uri: mongodb://localhost:27017  # ignoré si multitenant: true
    db_name: mydb
    collection_name: ingredients

  duckdb:
    path: data/ingredients.csv   # .csv | .parquet | .json | .arrow

soft_delete:
  retention_days: 30    # null = jamais supprimé physiquement
```

---

## Checklist pour une nouvelle entité

```
✅ src/arclith_sample/domain/models/              →  MaClasse(Entity)
✅ src/arclith_sample/domain/ports/               →  MaClasseRepository(Repository[MaClasse])   ← si requêtes spécifiques
✅ src/arclith_sample/application/use_cases/      →  MonUseCaseSpécifique                        ← si logique spécifique
✅ src/arclith_sample/application/services/       →  MaClasseService(BaseService[MaClasse])
✅ src/arclith_sample/adapters/input/schemas/     →  schémas Pydantic (Create, Update, Patch, Response)
✅ src/arclith_sample/adapters/output/            →  MaClasseRepository(InMemoryRepository / MongoDBRepository / DuckDBRepository)
✅ src/arclith_sample/adapters/input/fastapi/dependencies.py  →  inject_tenant_uri (multitenancy)
✅ src/arclith_sample/infrastructure/container.py →  brancher le repository et le service via Arclith
```
