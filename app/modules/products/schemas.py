from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_utils import to_camel


ProductUnit = Literal["piece", "kg"]


class CategoryRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: UUID
    name: str


class PhotoItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: UUID
    uri: str


class FillingItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # client does not have to send id
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=256)


class IngredientItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # client does not have to send id
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=256)

    # required if ingredient exists
    weight_grams: str = Field(alias="weightGrams", min_length=1, max_length=64)


class ProductCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=128)
    price: int = Field(ge=0)

    category_id: UUID | None = None
    recipe: str | None = None
    unit: ProductUnit

    # optional like frontend types
    fillings: list[FillingItem] | None = None
    ingredients: list[IngredientItem] | None = None

    photo_uris: list[str] | None = Field(default=None, alias="photoUris")


class ProductUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=128)
    price: int = Field(ge=0)

    category_id: UUID | None = None
    recipe: str | None = None
    unit: ProductUnit

    fillings: list[FillingItem] | None = None
    ingredients: list[IngredientItem] | None = None

    photo_uris: list[str] | None = Field(default=None, alias="photoUris")


class ProductRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: UUID
    name: str
    category: CategoryRead | None

    price: int
    fillings: list[FillingItem] | None = None
    ingredients: list[IngredientItem] | None = None
    recipe: str | None
    unit: ProductUnit

    # optional like frontend types
    photoes: list[PhotoItem] | None = None

    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")