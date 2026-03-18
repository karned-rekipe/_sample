from pydantic import BaseModel, Field, field_validator

from arclith.adapters.input.schemas.base_schema import BaseSchema


class IngredientCreateSchema(BaseModel):
    name: str = Field(
        ...,
        description="Nom de l'ingrédient.",
        examples = ["Farine de blé", "Sel fin"],
        min_length = 1
    )
    unit: str | None = Field(
        None,
        description="Unité de mesure (ex. g, kg, ml). None si non applicable.",
        examples = ["g", "kg", "ml", None],
        min_length = 1
    )

    @field_validator("name", mode = "before")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("unit", mode = "before")
    @classmethod
    def unit_not_empty(cls, v: str | None) -> str | None:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Unit cannot be empty when provided")
        return v


class IngredientPatchSchema(IngredientCreateSchema):
    name: str | None = Field(  # type: ignore[assignment]
        None,
        description="Nouveau nom de l'ingrédient. Ignoré si absent.",
        examples=["Farine complète", None],
    )


class IngredientUpdateSchema(IngredientCreateSchema):
    pass


class IngredientSchema(BaseSchema):
    name: str = Field(
        ...,
        description = "Nom de l'ingrédient.",
        examples = ["Farine de blé", "Sel fin"],
    )
    unit: str | None = Field(
        None,
        description = "Unité de mesure (ex. g, kg, ml). None si non applicable.",
        examples = ["g", "kg", "ml", None],
    )
