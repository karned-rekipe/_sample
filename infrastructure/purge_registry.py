from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class PurgeRegistry:
    """Registre des fonctions de purge par entité.

    Chaque entité enregistre sa fonction de purge via ``register()``.
    Un appel à ``purge_all()`` déclenche toutes les purges en parallèle.

    Usage::

        purge_registry.register("ingredients", service.purge)
        purge_registry.register("recipes", recipe_service.purge)

        results = await purge_registry.purge_all()
        # {"ingredients": 3, "recipes": 0}
    """

    def __init__(self) -> None:
        self._purgers: dict[str, Callable[[], Awaitable[int]]] = {}

    def register(self, name: str, fn: Callable[[], Awaitable[int]]) -> None:
        self._purgers[name] = fn

    async def purge_all(self) -> dict[str, int]:
        """Déclenche toutes les purges enregistrées en parallèle.

        Retourne ``{entity_name: purged_count}`` pour chaque entité.
        """
        if not self._purgers:
            return {}
        names = list(self._purgers)
        results = await asyncio.gather(*[self._purgers[n]() for n in names])
        return dict(zip(names, results))


purge_registry = PurgeRegistry()

