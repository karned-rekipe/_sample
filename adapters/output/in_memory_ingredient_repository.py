from kcrud.adapters.output.in_memory_repository import InMemoryRepository
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository


class InMemoryIngredientRepository(InMemoryRepository[Ingredient], IngredientRepository):
    async def find_by_name(self, name: str) -> list[Ingredient]:
        return [i for i in self._store.values() if name.lower() in i.name.lower()]
