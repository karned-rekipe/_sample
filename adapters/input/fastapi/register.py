from adapters.input.fastapi.routers import AdminRouter, IngredientRouter
from arclith import Arclith
from fastapi import FastAPI
from infrastructure.containers.ingredient_container import build_ingredient_service
from infrastructure.purge_registry import purge_registry


def register_routers(app: FastAPI, arclith: Arclith) -> None:
    service, logger = build_ingredient_service(arclith)
    purge_registry.register("ingredients", service.purge)
    app.include_router(IngredientRouter(service, logger).router)
    app.include_router(AdminRouter(purge_registry).router)
