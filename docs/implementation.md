# Implémenter une entité avec kcrud

Ce dossier est le projet de référence. Il montre comment brancher `kcrud` pour une entité concrète : **Ingredient**.

Chaque section correspond à un fichier à créer, dans l'ordre des couches (de l'intérieur vers l'extérieur).

---

## 1. `domain/models/` — L'entité

Hérite de `Entity`. Contient uniquement les champs métier et leur validation.

```python
# domain/models/ingredient.py
from dataclasses import dataclass
from kcrud.domain.models.entity import Entity


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

## 2. `domain/ports/` — Le port spécifique

Si ton entité a des requêtes au-delà du CRUD générique, déclare-les ici sous forme d'interface abstraite.

```python
# domain/ports/ingredient_repository.py
from abc import abstractmethod
from kcrud.domain.ports.repository import Repository
from domain.models.ingredient import Ingredient


class IngredientRepository(Repository[Ingredient]):
    @abstractmethod
    async def find_by_name(self, name: str) -> list[Ingredient]: ...
```

> Si ton entité n'a pas de requêtes spécifiques, utilise directement `Repository[T]` — pas besoin de ce fichier.

---

## 3. `application/use_cases/` — Les cas d'usage spécifiques

Les use cases génériques (create, read, update…) sont fournis par `kcrud`.  
Ajoute ici uniquement ce qui est propre à ton entité.

```python
# application/use_cases/find_by_name.py
from kcrud.domain.ports.logger import Logger
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository


class FindByNameUseCase:
    def __init__(self, repository: IngredientRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def execute(self, name: str) -> list[Ingredient]:
        self._logger.info("🔍 Finding ingredients by name", name = name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ Ingredients found", name = name, count = len(result))
        return result
```

---

## 4. `application/services/` — La façade de service

Étend `BaseService` pour exposer les méthodes aux adapters. Ne contient pas de logique — délègue aux use cases.

```python
# application/services/ingredient_service.py
from kcrud.application.services.base_service import BaseService
from kcrud.domain.ports.logger import Logger
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository
from application.use_cases import FindByNameUseCase


class IngredientService(BaseService[Ingredient]):
    def __init__(self, repository: IngredientRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._find_by_name_uc = FindByNameUseCase(repository, logger)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return await self._find_by_name_uc.execute(name)
```

> `BaseService` expose déjà : `create`, `read`, `update`, `delete`, `find_all`, `duplicate`, `purge`.

---

## 5. `adapters/input/schemas/` — Les schémas Pydantic

Séparent le modèle HTTP du modèle domaine. Un schéma par intention (création, mise à jour, réponse).

```python
# adapters/input/schemas/ingredient_schema.py
from kcrud.adapters.input.schemas.base_schema import BaseSchema


class IngredientCreateSchema(BaseModel):
    name: str
    unit: str | None = None


class IngredientSchema(BaseSchema):  # réponse — hérite de BaseSchema (uuid, timestamps…)
    name: str
    unit: str | None = None
```

> `BaseSchema` inclut automatiquement les champs de `Entity` dans la réponse.

---

## 6. `adapters/output/` — Les repositories concrets

Implémente le port en héritant du repository `kcrud` correspondant **et** du port spécifique.

```python
# adapters/output/in_memory_ingredient_repository.py
from kcrud.adapters.output.in_memory_repository import InMemoryRepository
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository


class InMemoryIngredientRepository(InMemoryRepository[Ingredient], IngredientRepository):
    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [i for i in self._store.values() if name.lower() in i.name.lower()]
```

Même pattern pour MongoDB :

```python
# adapters/output/mongodb_ingredient_repository.py
from kcrud.adapters.output.mongodb_repository import MongoDBRepository


class MongoDBIngredientRepository(MongoDBRepository[Ingredient], IngredientRepository):
    def __init__(self, config: MongoDBConfig) -> None:
        super().__init__(config, Ingredient)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [self._from_doc(doc) async for doc in self._collection.find({"name": {"$regex": name, "$options": "i"}})]
```

---

## 7. `infrastructure/container.py` — L'injection de dépendances

Lit la config et instancie les dépendances. C'est le seul endroit où tout se branche.

```python
def _build_repository(config: AppConfig) -> IngredientRepository:
    match config.adapters.repository:
        case "mongodb":
            return MongoDBIngredientRepository(...)
        case "duckdb":
            return DuckDBIngredientRepository(...)
        case _:
            return InMemoryIngredientRepository()


def build_ingredient_service() -> tuple[IngredientService, Logger]:
    config = load_config(_CONFIG_PATH)
    logger = ConsoleLogger()
    repository = _build_repository(config)
    return IngredientService(repository, logger, config.soft_delete.retention_days), logger
```

---

## 8. `config.yaml` — La configuration

Choisit le repository actif et configure les connexions.

```yaml
adapters:
  repository: memory    # memory | mongodb | duckdb

  mongodb:
    uri: mongodb://localhost:27017
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
✅ domain/models/         →  MaClasse(Entity)
✅ domain/ports/          →  MaClasseRepository(Repository[MaClasse])   ← si requêtes spécifiques
✅ application/use_cases/ →  MonUseCaseSpécifique                        ← si logique spécifique
✅ application/services/  →  MaClasseService(BaseService[MaClasse])
✅ adapters/input/schemas/ →  schémas Pydantic (Create, Update, Patch, Response)
✅ adapters/output/       →  MaClasseRepository(InMemoryRepository / MongoDBRepository / DuckDBRepository)
✅ infrastructure/container.py →  brancher le repository et le service
```

