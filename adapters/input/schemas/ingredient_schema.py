from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from kcrud.adapters.input.schemas.base_schema import BaseSchema


class IngredientCreateSchema(BaseModel):
    name: str
    unit: Optional[str] = None


class IngredientPatchSchema(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None


class IngredientUpdateSchema(BaseModel):
    uuid: UUID
    name: str
    unit: Optional[str] = None


class IngredientSchema(BaseSchema):
    name: str
    unit: Optional[str] = None

