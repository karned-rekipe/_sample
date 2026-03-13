from dataclasses import dataclass
from typing import Optional

from kcrud.domain.models.entity import Entity


@dataclass
class Ingredient(Entity):
    name: str = ""
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("Ingredient name cannot be empty")
        self.name = normalized_name

        if self.unit is not None:
            normalized_unit = self.unit.strip()
            if not normalized_unit:
                raise ValueError("Ingredient unit cannot be empty when provided")
            self.unit = normalized_unit


