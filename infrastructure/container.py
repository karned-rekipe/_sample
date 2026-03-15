from arclith import Arclith, MongoDBConfig
from domain.ports.ingredient_repository import IngredientRepository
from application.services.ingredient_service import IngredientService
def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, ...]:
    logger = arclith.logger
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb.repository import MongoDBIngredientRepository
            mongo = config.adapters.mongodb
            repo: IngredientRepository = MongoDBIngredientRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name),
                logger,
            )
        case "duckdb":
            from adapters.output.duckdb.repository import DuckDBIngredientRepository
            repo = DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            from adapters.output.memory.repository import InMemoryIngredientRepository
            repo = InMemoryIngredientRepository()
    return IngredientService(repo, logger, config.soft_delete.retention_days), logger
