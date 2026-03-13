from pathlib import Path

from kcrud.adapters.output.console_logger import ConsoleLogger
from kcrud.adapters.output.mongodb_config import MongoDBConfig
from kcrud.domain.ports.logger import Logger
from kcrud.infrastructure.config import AppConfig, load_config

from adapters.output.in_memory_ingredient_repository import InMemoryIngredientRepository
from domain.ports.ingredient_repository import IngredientRepository
from domain.services.ingredient_service import IngredientService

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _build_logger(config: AppConfig) -> Logger:
    return ConsoleLogger()


def _build_repository(config: AppConfig) -> IngredientRepository:
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb_ingredient_repository import MongoDBIngredientRepository
            if config.adapters.mongodb is None:
                raise ValueError("repository=mongodb mais aucune section [adapters.mongodb] dans config.yaml")
            mongo = config.adapters.mongodb
            return MongoDBIngredientRepository(MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name))
        case "duckdb":
            from adapters.output.duckdb_ingredient_repository import DuckDBIngredientRepository
            if config.adapters.duckdb is None:
                raise ValueError("repository=duckdb mais aucune section [adapters.duckdb] dans config.yaml")
            return DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            return InMemoryIngredientRepository()


def _build_ingredient_service(config: AppConfig) -> tuple[IngredientService, Logger]:
    logger = _build_logger(config)
    repository = _build_repository(config)
    return IngredientService(repository, logger, config.soft_delete.retention_days), logger


def build_ingredient_service() -> tuple[IngredientService, Logger]:
    return _build_ingredient_service(load_config(_CONFIG_PATH))
