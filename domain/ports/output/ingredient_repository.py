from abc import abstractmethod

from arclith.domain.ports.repository import Repository
from domain.models.ingredient import Ingredient


class IngredientRepository(Repository[Ingredient]):
    @abstractmethod
    async def find_by_name(self, name: str) -> list[Ingredient]:
        pass

    @abstractmethod
    async def find_page_by_name(self, name: str, offset: int = 0, limit: int | None = None) -> tuple[list[Ingredient], int]:
        """Return a page of ingredients matching name filter and the total count."""
        pass

