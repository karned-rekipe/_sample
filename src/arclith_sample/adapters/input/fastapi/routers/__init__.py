"""FastAPI routers."""

from arclith_sample.adapters.input.fastapi.routers.admin_router import AdminRouter
from arclith_sample.adapters.input.fastapi.routers.ingredient_router import IngredientRouter

__all__ = ["AdminRouter", "IngredientRouter"]

