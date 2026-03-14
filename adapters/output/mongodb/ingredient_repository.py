from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository
from kcrud.adapters.output.mongodb.config import MongoDBConfig
from kcrud.adapters.output.mongodb.repository import MongoDBRepository
from kcrud.domain.ports.logger import Logger


class MongoDBIngredientRepository(MongoDBRepository[Ingredient], IngredientRepository):
    def __init__(self, config: MongoDBConfig, logger: Logger) -> None:
        super().__init__(config, Ingredient, logger)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        async with self._collection() as col:
            return [
                self._from_doc(doc)
                async for doc in col.find({"name": {"$regex": name, "$options": "i"}})
            ]
