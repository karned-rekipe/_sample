from kcrud.adapters.output.mongodb_config import MongoDBConfig
from kcrud.adapters.output.mongodb_repository import MongoDBRepository
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository


class MongoDBIngredientRepository(MongoDBRepository[Ingredient], IngredientRepository):
    def __init__(self, config: MongoDBConfig) -> None:
        super().__init__(config, Ingredient)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [
            self._from_doc(doc)
            async for doc in self._collection.find({"name": {"$regex": name, "$options": "i"}})
        ]
