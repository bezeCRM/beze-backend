from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.repository import CategoriesRepository
from app.modules.products.models import Product, ProductUnit
from app.modules.products.repository import ProductsRepository


class ProductAlreadyExistsError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


JsonObject = Dict[str, Any]
JsonArray = List[JsonObject]


def _ensure_item_ids(items: Optional[JsonArray]) -> Optional[JsonArray]:
    # ensures every item has id and all ids are json-friendly strings
    if items is None:
        return None

    out: JsonArray = []
    for item in items:
        item_id = item.get("id")
        if not item_id:
            item = {**item, "id": str(uuid4())}
        else:
            item = {**item, "id": str(item_id)}
        out.append(item)
    return out


class ProductsService:
    def __init__(self) -> None:
        self._repo = ProductsRepository()

    async def list(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
        category_id: UUID | None,
    ) -> List[Product]:
        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError

        return await self._repo.list_products(
            session,
            owner_id=owner_id,
            limit=limit,
            offset=offset,
            category_id=category_id,
        )

    async def get_or_404(self, session: AsyncSession, *, owner_id: UUID, product_id: UUID) -> Product:
        obj = await self._repo.get_product(session, owner_id=owner_id, product_id=product_id)
        if obj is None:
            raise ProductNotFoundError
        return obj

    async def create(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        name: str,
        price: int,
        category_id: UUID | None,
        recipe: str | None,
        unit: ProductUnit,
        fillings: Optional[JsonArray],
        ingredients: Optional[JsonArray],
        photo_uris: List[str],
    ) -> Product:
        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError

        fillings = _ensure_item_ids(fillings)
        ingredients = _ensure_item_ids(ingredients)

        try:
            obj = Product(
                owner_id=owner_id,
                name=name,
                price=price,
                category_id=category_id,
                recipe=recipe,
                unit=unit,
                fillings=fillings,
                ingredients=ingredients,
            )
            session.add(obj)
            await session.flush()

            await self._repo.replace_photos(session, product_id=obj.id, photo_uris=photo_uris)

            await session.commit()
            return await self.get_or_404(session, owner_id=owner_id, product_id=obj.id)
        except IntegrityError:
            await session.rollback()
            raise ProductAlreadyExistsError

    async def update(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        product_id: UUID,
        name: str,
        price: int,
        category_id: UUID | None,
        recipe: str | None,
        unit: ProductUnit,
        fillings: Optional[JsonArray],
        ingredients: Optional[JsonArray],
        photo_uris: List[str],
    ) -> Product:
        obj = await self.get_or_404(session, owner_id=owner_id, product_id=product_id)

        if category_id is not None:
            category = await CategoriesRepository.get(session, owner_id=owner_id, category_id=category_id)
            if category is None:
                raise CategoryNotFoundError

        fillings = _ensure_item_ids(fillings)
        ingredients = _ensure_item_ids(ingredients)

        obj.name = name
        obj.price = price
        obj.category_id = category_id
        obj.recipe = recipe
        obj.unit = unit
        obj.fillings = fillings
        obj.ingredients = ingredients
        obj.updated_at = datetime.now(timezone.utc)

        try:
            session.add(obj)
            await session.flush()

            await self._repo.replace_photos(session, product_id=obj.id, photo_uris=photo_uris)

            await session.commit()
            return await self.get_or_404(session, owner_id=owner_id, product_id=product_id)
        except IntegrityError:
            await session.rollback()
            raise ProductAlreadyExistsError

    async def delete(self, session: AsyncSession, *, owner_id: UUID, product_id: UUID) -> None:
        obj = await self.get_or_404(session, owner_id=owner_id, product_id=product_id)
        await session.delete(obj)
        await session.commit()