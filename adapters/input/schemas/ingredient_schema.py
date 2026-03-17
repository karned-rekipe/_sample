from pydantic import BaseModel, Field
from typing import Optional

from arclith.adapters.input.schemas.base_schema import BaseSchema


class IngredientCreateSchema(BaseModel):
    name: str = Field(
        min_length=1,
        description="Nom de l'ingrédient.",
        examples=["Farine de blé", "Sel fin"],
    )
    unit: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Unité de mesure (ex. g, kg, ml). None si non applicable.",
        examples=["g", "kg", "ml", None],
    )


class IngredientPatchSchema(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Nouveau nom de l'ingrédient. Ignoré si absent.",
        examples=["Farine complète", None],
    )
    unit: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Nouvelle unité de mesure. Ignoré si absent.",
        examples=["g", None],
    )


class IngredientUpdateSchema(BaseModel):
    name: str = Field(
        min_length=1,
        description="Nom de l'ingrédient.",
        examples=["Farine de blé", "Sel fin"],
    )
    unit: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Unité de mesure. None si non applicable.",
        examples=["g", "kg", "ml", None],
    )


class IngredientSchema(BaseSchema):
    name: str = Field(
        description="Nom de l'ingrédient.",
        examples=["Farine de blé", "Sel fin"],
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unité de mesure. None si non applicable.",
        examples=["g", "kg", "ml", None],
    )
