from pydantic import BaseModel, Field

class IngredientCreateSchema(BaseModel):
    name: str = Field(
        ...,
        description="Nom de l'ingrédient.",
        examples = ["Farine de blé", "Sel fin"]
    )

    unit: str | None = Field(
        None,
        description="Unité de mesure (ex. g, kg, ml). None si non applicable.",
        examples = ["g", "kg", "ml", None]
    )


class IngredientPatchSchema(IngredientCreateSchema):
    name: str | None = Field(  # type: ignore[assignment]
        None,
        description="Nouveau nom de l'ingrédient. Ignoré si absent.",
        examples=["Farine complète", None],
    )


class IngredientUpdateSchema(IngredientCreateSchema):
    pass


class IngredientSchema(IngredientCreateSchema):
    pass
