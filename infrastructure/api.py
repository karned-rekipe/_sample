from fastapi import FastAPI

from adapters.input.ingredient_fastapi import IngredientRouter
from kcrud.domain.ports.logger import Logger
from infrastructure.container import build_ingredient_service


def create_api() -> tuple[FastAPI, Logger]:
    api = FastAPI()

    ingredient_service, logger = build_ingredient_service()
    ingredient_router = IngredientRouter(ingredient_service, logger)

    api.include_router(ingredient_router.router)

    return api, logger

