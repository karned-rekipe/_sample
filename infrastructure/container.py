from arclith import Arclith, MongoDBConfig
from domain.ports.ingredient_repository import IngredientRepository
from application.services.ingredient_service import IngredientService
from logging import Logger
def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, Logger]:
    logger = arclith.logger
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb.repository import MongoDBIngredientRepository
            mongo = getattr(config.adapters, "mongodb", None)
            if mongo is None:
                raise ValueError(
                    "MongoDB adapter configuration 'adapters.mongodb' is required when "
                    "'adapters.repository' is set to 'mongodb'."
                )
            repo: IngredientRepository = MongoDBIngredientRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name),
                logger,
            )
        case "duckdb":
            from adapters.output.duckdb.repository import DuckDBIngredientRepository
            duckdb_config = getattr(config.adapters, "duckdb", None)
            if duckdb_config is None or getattr(duckdb_config, "path", None) is None:
                raise ValueError(
                    "Invalid configuration: adapters.repository is 'duckdb' but "
                    "config.adapters.duckdb.path is not set."
                )
            repo = DuckDBIngredientRepository(duckdb_config.path)
        case _:
            from adapters.output.memory.repository import InMemoryIngredientRepository
            repo = InMemoryIngredientRepository()
    return IngredientService(repo, logger, config.soft_delete.retention_days), logger
