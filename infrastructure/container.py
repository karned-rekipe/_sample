from arclith import Arclith, MongoDBConfig
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository
from domain.services.ingredient_service import IngredientService
def build_ingredient_service(arclith: Arclith) -> tuple[IngredientService, ...]:
    logger = arclith.logger
    config = arclith.config
    match config.adapters.repository:
        case "mongodb":
            from adapters.output.mongodb_ingredient_repository import MongoDBIngredientRepository
            mongo = config.adapters.mongodb
            repo: IngredientRepository = MongoDBIngredientRepository(
                MongoDBConfig(uri=mongo.uri, db_name=mongo.db_name, collection_name=mongo.collection_name),
                logger,
            )
        case "duckdb":
            from adapters.output.duckdb_ingredient_repository import DuckDBIngredientRepository
            repo = DuckDBIngredientRepository(config.adapters.duckdb.path)
        case _:
            from adapters.output.in_memory_ingredient_repository import InMemoryIngredientRepository
            repo = InMemoryIngredientRepository()
    return IngredientService(repo, logger, config.soft_delete.retention_days), logger
