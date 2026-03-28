"""FastAPI routers."""

from adapters.input.fastapi.routers.admin_router import AdminRouter
from adapters.input.fastapi.routers.ingredient_router import IngredientRouter

__all__ = ["AdminRouter", "IngredientRouter"]

