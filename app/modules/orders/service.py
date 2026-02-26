from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order, OrderLine
from app.modules.orders.repository import OrdersRepository
from app.modules.orders.schemas import OrderPatch
from app.modules.products.models import Product, ProductUnit


class OrderNotFoundError(Exception):
    pass


class ProductNotFoundInOrderError(Exception):
    pass


class InvalidFillingError(Exception):
    pass


def _ensure_photo_item_ids(items: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if items is None:
        return None

    out: list[dict[str, Any]] = []
    for item in items:
        if "id" not in item or not item["id"]:
            out.append({**item, "id": str(uuid4())})
        else:
            out.append({**item, "id": str(item["id"])})
    return out


def _money_mul(price: int, amount: Decimal) -> int:
    total = (Decimal(price) * amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if total < 0:
        return 0
    return int(total)


def _calc_total_price(
    *,
    lines: list[OrderLine],
    decor_prices: list[dict[str, Any]] | None,
    extra: dict[str, Any] | None,
) -> int:
    lines_sum = 0
    for l in lines:
        lines_sum += int(l.price)

    decor_sum = 0
    if decor_prices is not None:
        for d in decor_prices:
            decor_sum += int(d.get("price") or 0)

    extra_add = 0
    extra_discount = 0
    if extra is not None:
        extra_add += int(extra.get("delivery") or 0)
        extra_add += int(extra.get("urgency") or 0)
        extra_add += int(extra.get("other") or 0)
        extra_discount += int(extra.get("discount") or 0)

    total = lines_sum + decor_sum + extra_add - extra_discount
    return max(total, 0)


def _validate_filling(product: Product, filling_id: UUID | None) -> dict[str, Any] | None:
    if filling_id is None:
        return None

    fillings = product.fillings or []
    for f in fillings:
        try:
            if f.get("id") == str(filling_id) or f.get("id") == filling_id:
                return {"id": str(filling_id), "name": f.get("name")}
        except AttributeError:
            continue

    raise InvalidFillingError


def _next_last_payment_at(
    *,
    current: datetime | None,
    old_paid_amount: int,
    new_paid_amount: int,
) -> datetime | None:
    if new_paid_amount <= 0:
        return None
    if new_paid_amount != old_paid_amount:
        return datetime.now(timezone.utc)
    return current


class OrdersService:
    def __init__(self) -> None:
        self._repo = OrdersRepository()

    async def list(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        limit: int,
        offset: int,
    ) -> list[Order]:
        return await self._repo.list_orders(session, owner_id=owner_id, limit=limit, offset=offset)

    async def get_or_404(self, session: AsyncSession, *, owner_id: UUID, order_id: UUID) -> Order:
        obj = await self._repo.get_order(session, owner_id=owner_id, order_id=order_id)
        if obj is None:
            raise OrderNotFoundError
        return obj

    async def build_lines_from_input(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        items: list[dict[str, Any]],
    ) -> list[OrderLine]:
        product_ids = {UUID(str(i["product_id"])) for i in items}
        products_by_id = await self._repo.get_products_by_ids(session, owner_id=owner_id, product_ids=product_ids)
        if len(products_by_id) != len(product_ids):
            raise ProductNotFoundInOrderError

        lines: list[OrderLine] = []
        for it in items:
            product_id = UUID(str(it["product_id"]))
            amount_raw = it["amount"]
            filling_id = it.get("filling_id")

            product = products_by_id[product_id]

            amount = Decimal(str(amount_raw))
            if amount <= 0:
                raise ValueError("amount must be > 0")

            if product.unit == ProductUnit.piece:
                if amount != amount.to_integral_value():
                    raise ValueError("piece product amount must be integer")

            line_total = _money_mul(product.price, amount)
            filling_json = _validate_filling(product, filling_id)

            lines.append(
                OrderLine(
                    order_id=UUID(int=0),
                    product_id=product_id,
                    amount=float(amount),
                    filling=filling_json,
                    price=line_total,
                    unit=product.unit,
                )
            )

        return lines

    async def create(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        order: Order,
        lines: list[OrderLine],
    ) -> Order:
        order.references = _ensure_photo_item_ids(order.references)
        order.total_price = _calc_total_price(lines=lines, decor_prices=order.decor_prices, extra=order.extra)

        if order.paid_amount > 0:
            order.last_payment_at = datetime.now(timezone.utc)
        else:
            order.last_payment_at = None

        session.add(order)
        await session.flush()

        for l in lines:
            l.order_id = order.id
            session.add(l)

        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, order_id=order.id)

    async def update(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        order_id: UUID,
        patch: Order,
        lines: list[OrderLine],
    ) -> Order:
        obj = await self.get_or_404(session, owner_id=owner_id, order_id=order_id)

        old_paid = obj.paid_amount

        obj.name = patch.name
        obj.client_name = patch.client_name
        obj.client_phone = patch.client_phone
        obj.order_platform = patch.order_platform
        obj.delivery_type = patch.delivery_type
        obj.address = patch.address
        obj.date = patch.date
        obj.time = patch.time
        obj.notes = patch.notes

        obj.decor_prices = patch.decor_prices
        obj.extra = patch.extra
        obj.references = _ensure_photo_item_ids(patch.references)

        obj.status = patch.status
        obj.paid_amount = patch.paid_amount
        obj.in_planner = patch.in_planner

        obj.last_payment_at = _next_last_payment_at(
            current=obj.last_payment_at,
            old_paid_amount=old_paid,
            new_paid_amount=obj.paid_amount,
        )

        obj.updated_at = datetime.now(timezone.utc)
        obj.total_price = _calc_total_price(lines=lines, decor_prices=obj.decor_prices, extra=obj.extra)

        await self._repo.delete_lines_by_order_id(session, order_id=obj.id)
        for l in lines:
            l.order_id = obj.id
        await self._repo.insert_lines(session, lines=lines)

        session.add(obj)
        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, order_id=order_id)

    async def patch(
        self,
        session: AsyncSession,
        *,
        owner_id: UUID,
        order_id: UUID,
        payload: OrderPatch,
    ) -> Order:
        obj = await self.get_or_404(session, owner_id=owner_id, order_id=order_id)
        fields = payload.model_fields_set
        if not fields:
            raise ValueError("empty patch")

        old_paid = obj.paid_amount

        if "name" in fields:
            obj.name = payload.name

        if "client_name" in fields and payload.client_name is not None:
            obj.client_name = payload.client_name

        if "client_phone" in fields:
            obj.client_phone = payload.client_phone

        if "order_platform" in fields:
            obj.order_platform = payload.order_platform

        if "delivery_type" in fields and payload.delivery_type is not None:
            obj.delivery_type = obj.delivery_type.__class__(payload.delivery_type)

            if payload.delivery_type == "pickup":
                obj.address = None

        if "address" in fields:
            obj.address = payload.address

        if "date" in fields and payload.date is not None:
            obj.date = obj.date.__class__.fromisoformat(payload.date)  # type: ignore[attr-defined]

        if "time" in fields and payload.time is not None:
            obj.time = obj.time.__class__.fromisoformat(payload.time)  # type: ignore[attr-defined]

        if "notes" in fields:
            obj.notes = payload.notes

        need_recalc_total = False
        new_lines: list[OrderLine] | None = None

        if "decor_prices" in fields:
            if payload.decor_prices is None:
                obj.decor_prices = None
            else:
                obj.decor_prices = [d.model_dump(mode="json", by_alias=True) for d in payload.decor_prices]
            need_recalc_total = True

        if "extra" in fields:
            if payload.extra is None:
                obj.extra = None
            else:
                obj.extra = payload.extra.model_dump(mode="json", by_alias=True)
            need_recalc_total = True

        if "references" in fields:
            if payload.references is None:
                obj.references = None
            else:
                obj.references = _ensure_photo_item_ids([r.model_dump(mode="json", by_alias=True) for r in payload.references])

        if "status" in fields and payload.status is not None:
            obj.status = obj.status.__class__(payload.status)

        if "in_planner" in fields and payload.in_planner is not None:
            obj.in_planner = payload.in_planner

        if "paid_amount" in fields:
            if payload.paid_amount is None:
                raise ValueError("paidAmount must be provided")
            obj.paid_amount = payload.paid_amount
            obj.last_payment_at = _next_last_payment_at(
                current=obj.last_payment_at,
                old_paid_amount=old_paid,
                new_paid_amount=obj.paid_amount,
            )

        if "products" in fields:
            if payload.products is None or len(payload.products) == 0:
                raise ValueError("products must be non-empty")
            items = [
                {"product_id": p.product_id, "amount": p.amount, "filling_id": p.filling_id}
                for p in payload.products
            ]
            new_lines = await self.build_lines_from_input(session, owner_id=owner_id, items=items)
            need_recalc_total = True

        if need_recalc_total:
            if new_lines is None:
                existing_lines = await self._repo.list_lines_by_order_id(session, order_id=obj.id)
                obj.total_price = _calc_total_price(lines=existing_lines, decor_prices=obj.decor_prices, extra=obj.extra)
            else:
                obj.total_price = _calc_total_price(lines=new_lines, decor_prices=obj.decor_prices, extra=obj.extra)

        if new_lines is not None:
            await self._repo.delete_lines_by_order_id(session, order_id=obj.id)
            for l in new_lines:
                l.order_id = obj.id
            await self._repo.insert_lines(session, lines=new_lines)

        obj.updated_at = datetime.now(timezone.utc)

        session.add(obj)
        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, order_id=order_id)

    async def delete(self, session: AsyncSession, *, owner_id: UUID, order_id: UUID) -> None:
        obj = await self.get_or_404(session, owner_id=owner_id, order_id=order_id)
        await self._repo.delete_lines_by_order_id(session, order_id=obj.id)
        await session.delete(obj)
        await session.commit()