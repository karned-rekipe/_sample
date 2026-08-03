from arclith_sample.application.services.ingredient_service import IngredientService
from arclith import Arclith, RepositoryRegistry
from arclith.adapters.outbound.mongodb.config import MongoDBConfig
from arclith.domain.ports.outbound.logger import Logger
from arclith.infrastructure.config import AppConfig
from arclith_sample.domain.models.ingredient import Ingredient
from arclith_sample.domain.ports.outbound.ingredient_repository import IngredientRepository


def _build_memory(_cfg: AppConfig, _entity_class: type[Ingredient], _log: Logger) -> IngredientRepository:
    from arclith_sample.adapters.outbound.memory.repository import InMemoryIngredientRepository
    return InMemoryIngredientRepository()


def _build_mongodb(cfg: AppConfig, _entity_class: type[Ingredient], log: Logger) -> IngredientRepository:
    from arclith_sample.adapters.outbound.mongodb.repository import MongoDBIngredientRepository
    mongo = cfg.adapters.mongodb
    if mongo is None:
        raise ValueError("MongoDB settings are required when repository=mongodb")
    return MongoDBIngredientRepository(
        MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name),
        log,
    )


def _build_duckdb(cfg: AppConfig, _entity_class: type[Ingredient], _log: Logger) -> IngredientRepository:
    from arclith_sample.adapters.outbound.duckdb.repository import DuckDBIngredientRepository
    duckdb = cfg.adapters.duckdb
    if duckdb is None:
        raise ValueError("DuckDB settings are required when repository=duckdb")
    return DuckDBIngredientRepository(duckdb.path)


_repository_registry: RepositoryRegistry[Ingredient, IngredientRepository] = (
    RepositoryRegistry[Ingredient, IngredientRepository]()
    .register("memory", _build_memory)
    .register("mongodb", _build_mongodb)
    .register("duckdb", _build_duckdb)
)


def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, Logger]:
    arclith.logger.info("🗄️ Repository adapter selected", adapter=arclith.config.adapters.repository)
    repo: IngredientRepository = arclith.repository(Ingredient, registry=_repository_registry)
    return IngredientService(repo, arclith.logger, arclith.config.soft_delete.retention_days), arclith.logger
