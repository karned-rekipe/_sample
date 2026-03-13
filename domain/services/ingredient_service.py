from kcrud.domain.ports.logger import Logger
from kcrud.domain.services.base_service import BaseService
from domain.models.ingredient import Ingredient
from domain.ports.ingredient_repository import IngredientRepository


class IngredientService(BaseService[Ingredient]):
    def __init__(self, repository: IngredientRepository, logger: Logger, retention_days: float | None = None) -> None:
        super().__init__(repository, logger, retention_days)
        self._repository = repository
        self._logger = logger

    async def find_by_name(self, name: str) -> list[Ingredient]:
        self._logger.info("🔍 Finding ingredients by name", name=name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ Ingredients found", name=name, count=len(result))
        return result
