from pathlib import Path

from adapters.output.memory.ingredient_repository import InMemoryIngredientRepository
from application.services.ingredient_service import IngredientService
from domain.ports.ingredient_repository import IngredientRepository
from kcrud.adapters.output.console.logger import ConsoleLogger
from kcrud.adapters.output.mongodb.config import MongoDBConfig
from kcrud.domain.ports.logger import Logger
from kcrud.infrastructure.config import AppConfig, load_config

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _build_logger() -> Logger:
    return ConsoleLogger()


def _build_repository(config: AppConfig, logger: Logger) -> IngredientRepository:
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb.ingredient_repository import MongoDBIngredientRepository
            mongo = config.adapters.mongodb
            return MongoDBIngredientRepository(MongoDBConfig(
                db_name = mongo.db_name,
                collection_name = mongo.collection_name,
                uri = mongo.uri,
            ), logger)
        case "duckdb":
            from adapters.output.duckdb.ingredient_repository import DuckDBIngredientRepository
            return DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            return InMemoryIngredientRepository()


def build_ingredient_service() -> tuple[IngredientService, Logger]:
    config = load_config(_CONFIG_PATH)
    logger = _build_logger()
    repository = _build_repository(config, logger)
    return IngredientService(repository, logger, config.soft_delete.retention_days), logger
