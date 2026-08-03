import pytest
from arclith.infrastructure.config import (
    AppConfig,
    AdaptersSettings,
    DuckDBSettings,
    MongoDBSettings,
)
from arclith.infrastructure.repository_factory import RepositoryRegistry, build_repository
from arclith.domain.models.entity import Entity
from arclith.domain.ports.outbound.logger import Logger
from arclith.domain.ports.outbound.repository import Repository
from arclith_sample.application.services.ingredient_service import IngredientService
from arclith_sample.infrastructure.containers.ingredient_container import build_ingredient_service


class StubArclith:
    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger

    def repository[T: Entity](
        self,
        entity_class: type[T],
        *,
        registry: RepositoryRegistry[T, Repository[T]] | None = None,
    ) -> Repository[T]:
        return build_repository(self.config, entity_class, self.logger, registry=registry)


def _arclith(config: AppConfig, logger: Logger) -> StubArclith:
    return StubArclith(config, logger)


def test_memory_creates_service(logger):
    arclith = _arclith(AppConfig(adapters=AdaptersSettings(repository="memory")), logger)
    service, log = build_ingredient_service(arclith)
    assert isinstance(service, IngredientService)
    assert log is logger


def test_mongodb_creates_service(logger):
    config = AppConfig(adapters=AdaptersSettings(
        repository="mongodb",
        mongodb=MongoDBSettings(uri="mongodb://localhost:27017", db_name="test"),
    ))
    service, log = build_ingredient_service(_arclith(config, logger))
    assert isinstance(service, IngredientService)


def test_duckdb_creates_service(logger, tmp_path):
    config = AppConfig(adapters=AdaptersSettings(
        repository="duckdb",
        duckdb=DuckDBSettings(path=str(tmp_path) + "/"),
    ))
    service, log = build_ingredient_service(_arclith(config, logger))
    assert isinstance(service, IngredientService)


def test_mongodb_missing_config_raises():
    with pytest.raises(ValueError, match="repository=mongodb"):
        AdaptersSettings(repository="mongodb", mongodb=None)


def test_duckdb_missing_config_raises():
    with pytest.raises(ValueError, match="repository=duckdb"):
        AdaptersSettings(repository="duckdb", duckdb=None)
