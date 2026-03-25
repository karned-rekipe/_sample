from arclith.adapters.output.duckdb.repository import DuckDBRepository
from domain.models.ingredient import Ingredient
from domain.ports.output.ingredient_repository import IngredientRepository


class DuckDBIngredientRepository(DuckDBRepository[Ingredient], IngredientRepository):
    def __init__(self, path: str) -> None:
        super().__init__(path, Ingredient)

    # noinspection SqlNoDataSourceInspection
    async def find_by_name(self, name: str) -> list[Ingredient]:
        rows = self._fetch(
            f"SELECT * FROM {self._table} WHERE deleted_at IS NULL AND lower(name) LIKE ?",  # nosec B608
            [f"%{name.lower()}%"],
        )
        return [self._row_to_entity(r) for r in rows]

    # noinspection SqlNoDataSourceInspection
    async def find_page_by_name(self, name: str, offset: int = 0, limit: int | None = None) -> tuple[list[Ingredient], int]:
        """Single-query pagination with name filter via window function."""
        limit_clause = f"LIMIT {limit}" if limit is not None else ""
        rows = self._fetch(
            f"SELECT *, COUNT(*) OVER () AS __total FROM {self._table} "  # nosec B608
            f"WHERE deleted_at IS NULL AND lower(name) LIKE ? "
            f"ORDER BY rowid OFFSET {offset} {limit_clause}",
            [f"%{name.lower()}%"],
        )
        total = int(rows[0]["__total"]) if rows else 0
        return [self._row_to_entity({k: v for k, v in r.items() if k != "__total"}) for r in rows], total

