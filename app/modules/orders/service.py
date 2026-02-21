from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order, OrderLine, OrderPaymentStatus
from app.modules.orders.repository import OrdersRepository
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


def _calc_payment_status(total_price: int, paid_amount: int) -> OrderPaymentStatus:
    if paid_amount <= 0:
        return OrderPaymentStatus.unpaid
    if paid_amount >= total_price and total_price > 0:
        return OrderPaymentStatus.paid
    return OrderPaymentStatus.partial


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
        order.payment_status = _calc_payment_status(order.total_price, order.paid_amount)

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
        obj.last_payment_at = patch.last_payment_at

        obj.updated_at = datetime.now(timezone.utc)
        obj.total_price = _calc_total_price(lines=lines, decor_prices=obj.decor_prices, extra=obj.extra)
        obj.payment_status = _calc_payment_status(obj.total_price, obj.paid_amount)

        await self._repo.delete_lines_by_order_id(session, order_id=obj.id)
        for l in lines:
            l.order_id = obj.id
        await self._repo.insert_lines(session, lines=lines)

        session.add(obj)
        await session.commit()
        return await self.get_or_404(session, owner_id=owner_id, order_id=order_id)

    async def delete(self, session: AsyncSession, *, owner_id: UUID, order_id: UUID) -> None:
        obj = await self.get_or_404(session, owner_id=owner_id, order_id=order_id)
        await self._repo.delete_lines_by_order_id(session, order_id=obj.id)
        await session.delete(obj)
        await session.commit()