"""FastAPI routers."""

from arclith_sample.adapters.inbound.fastapi.routers.admin_router import AdminRouter
from arclith_sample.adapters.inbound.fastapi.routers.ingredient_router import IngredientRouter

__all__ = ["AdminRouter", "IngredientRouter"]

