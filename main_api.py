from pathlib import Path
from arclith import Arclith
from adapters.input.fastapi.router import IngredientRouter
from infrastructure.container import build_ingredient_service
arclith = Arclith(Path(__file__).parent / "config.yaml")
service, logger = build_ingredient_service(arclith)
app = arclith.fastapi()
app.include_router(IngredientRouter(service, logger).router)
if __name__ == "__main__":
    arclith.run_api("main_api:app")
