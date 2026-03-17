from arclith import Arclith
from arclith.adapters.output.mongodb.config import MongoDBConfig
from arclith.domain.ports.logger import Logger
from application.services.ingredient_service import IngredientService


def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, Logger]:
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb.repository import MongoDBIngredientRepository
            mongo = config.adapters.mongodb
            repo = MongoDBIngredientRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name),
                arclith.logger,
            )
        case "duckdb":
            from adapters.output.duckdb.repository import DuckDBIngredientRepository
            repo = DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            from adapters.output.memory.repository import InMemoryIngredientRepository
            repo = InMemoryIngredientRepository()
    return IngredientService(repo, arclith.logger, config.soft_delete.retention_days), arclith.logger

