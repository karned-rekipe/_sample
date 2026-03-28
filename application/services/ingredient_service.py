from application.use_cases import FindByNameUseCase
from arclith import BaseService, Logger
from domain.models.ingredient import Ingredient
from domain.ports.output.ingredient_repository import IngredientRepository


class IngredientService(BaseService[Ingredient]):
    def __init__(self, repository: IngredientRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._ingredient_repo = repository
        self._find_by_name_uc = FindByNameUseCase(repository, logger)

    async def find_by_name(self, name: str) -> list[Ingredient]:
        return await self._find_by_name_uc.execute(name)

    async def find_page_filtered(self, name: str | None = None, offset: int = 0, limit: int | None = None) -> tuple[list[Ingredient], int]:
        """Return a page of ingredients (optionally filtered by name) and total count."""
        if name:
            return await self._ingredient_repo.find_page_by_name(name, offset, limit)
        return await self._ingredient_repo.find_page(offset, limit)

