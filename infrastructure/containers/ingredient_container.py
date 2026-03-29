from __future__ import annotations

from typing import cast

from application.services.ingredient_service import IngredientService
from arclith import Arclith, AdapterRegistry
from arclith.adapters.output.mongodb.config import MongoDBConfig
from arclith.domain.ports.logger import Logger
from arclith.domain.ports.repository import Repository
from arclith.infrastructure.config import AppConfig
from domain.models.ingredient import Ingredient
from domain.ports.output.ingredient_repository import IngredientRepository


def _build_memory(cfg: AppConfig, log: Logger) -> Repository[Ingredient]:
    from adapters.output.memory.repository import InMemoryIngredientRepository
    return InMemoryIngredientRepository()


def _build_mongodb(cfg: AppConfig, log: Logger) -> Repository[Ingredient]:
    from adapters.output.mongodb.repository import MongoDBIngredientRepository
    mongo = cfg.adapters.mongodb
    if mongo is None:
        raise RuntimeError("MongoDB settings are required when repository=mongodb")
    return MongoDBIngredientRepository(
        MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name),
        log,
    )


def _build_duckdb(cfg: AppConfig, log: Logger) -> Repository[Ingredient]:
    from adapters.output.duckdb.repository import DuckDBIngredientRepository
    duckdb = cfg.adapters.duckdb
    if duckdb is None:
        raise RuntimeError("DuckDB settings are required when repository=duckdb")
    return DuckDBIngredientRepository(duckdb.path)


_registry = cast(
    AdapterRegistry[Ingredient],
    AdapterRegistry[Ingredient]()
    .register("memory", _build_memory)  # type: ignore[arg-type]
    .register("mongodb", _build_mongodb)  # type: ignore[arg-type]
    .register("duckdb", _build_duckdb)  # type: ignore[arg-type]
)


def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, Logger]:
    arclith.logger.info("🗄️ Repository adapter selected", adapter=arclith.config.adapters.repository)
    repo: IngredientRepository = cast(IngredientRepository, _registry.build(arclith.config, arclith.logger))
    return IngredientService(repo, arclith.logger, arclith.config.soft_delete.retention_days), arclith.logger
