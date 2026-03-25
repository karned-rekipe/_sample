from arclith.domain.ports.logger import Logger
from domain.models.ingredient import Ingredient
from domain.ports.output.ingredient_repository import IngredientRepository


class FindByNameUseCase:
    def __init__(self, repository: IngredientRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def execute(self, name: str) -> list[Ingredient]:
        self._logger.info("🔍 Finding ingredients by name", name=name)
        result = [i for i in await self._repository.find_by_name(name) if not i.is_deleted]
        self._logger.info("✅ Ingredients found", name=name, count=len(result))
        return result

