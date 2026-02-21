from __future__ import annotations

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.modules.orders.models import Order, OrderDeliveryType, OrderStatus
from app.modules.orders.repository import OrdersRepository
from app.modules.orders.schemas import (
    OrderCreate,
    OrderProductLineRead,
    OrderRead,
    OrderUpdate,
    OrderDecorPriceRead,
)
from app.modules.orders.service import (
    InvalidFillingError,
    OrderNotFoundError,
    OrdersService,
    ProductNotFoundInOrderError,
)
from app.modules.products.repository import ProductsRepository
from app.modules.products.schemas import ProductRead
from app.modules.users.models import User

router = APIRouter(prefix="/orders", tags=["orders"])


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def _to_product_read(*, product, category, photoes) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        category=category,
        price=product.price,
        fillings=product.fillings,
        ingredients=product.ingredients,
        recipe=product.recipe,
        unit=product.unit,
        photoes=photoes if photoes else None,
        createdAt=product.created_at,
        updatedAt=product.updated_at,
    )


async def _build_order_read(
    *,
    session: AsyncSession,
    owner_id: UUID,
    order: Order,
    lines,
) -> OrderRead:
    repo_orders = OrdersRepository()
    repo_products = ProductsRepository()

    product_ids = {l.product_id for l in lines}
    products_by_id = await repo_orders.get_products_by_ids(session, owner_id=owner_id, product_ids=product_ids)

    category_ids = {p.category_id for p in products_by_id.values() if p.category_id is not None}
    categories_by_id = await repo_products.get_categories_by_ids(session, owner_id=owner_id, category_ids=category_ids)
    photos_by_pid = await repo_products.get_photos_by_product_ids(session, product_ids=list(products_by_id.keys()))

    products_read: list[OrderProductLineRead] = []
    for l in lines:
        prod = products_by_id.get(l.product_id)
        if prod is None:
            continue

        cat = categories_by_id.get(prod.category_id) if prod.category_id is not None else None
        prod_read = _to_product_read(product=prod, category=cat, photoes=photos_by_pid.get(prod.id, []))

        products_read.append(
            OrderProductLineRead(
                id=l.id,
                product=prod_read,
                amount=float(l.amount),
                filling=l.filling,
                price=l.price,
                unit=prod.unit.value,
            )
        )

    decor_read: list[OrderDecorPriceRead] | None = None
    if order.decor_prices is not None:
        decor_read = []
        for d in order.decor_prices:
            try:
                pid = UUID(str(d.get("productId") or d.get("product_id") or d.get("id")))
            except (ValueError, TypeError):
                continue
            prod = products_by_id.get(pid)
            decor_read.append(
                OrderDecorPriceRead(
                    id=pid,
                    name=None if prod is None else prod.name,
                    price=int(d.get("price") or 0),
                )
            )

    return OrderRead(
        id=order.id,
        name=order.name,
        clientName=order.client_name,
        clientPhone=order.client_phone,
        orderPlatform=order.order_platform,
        deliveryType=order.delivery_type.value,
        address=order.address,
        date=order.date.isoformat(),
        time=order.time.isoformat(timespec="minutes"),
        products=products_read,
        decorPrices=decor_read,
        extra=order.extra,
        notes=order.notes,
        references=order.references,
        paymentStatus=order.payment_status.value,
        status=order.status.value,
        paidAmount=order.paid_amount,
        inPlanner=order.in_planner,
        totalPrice=order.total_price,
        lastPaymentAt=order.last_payment_at,
        createdAt=order.created_at,
        updatedAt=order.updated_at,
    )


@router.get("", response_model=list[OrderRead])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    svc = OrdersService()
    repo = OrdersRepository()

    orders = await svc.list(session, owner_id=current_user.id, limit=limit, offset=offset)
    lines_by_oid = await repo.get_lines_by_order_ids(session, order_ids=[o.id for o in orders])

    out: list[OrderRead] = []
    for o in orders:
        out.append(
            await _build_order_read(
                session=session,
                owner_id=current_user.id,
                order=o,
                lines=lines_by_oid.get(o.id, []),
            )
        )
    return out


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = OrdersService()
    repo = OrdersRepository()

    try:
        o = await svc.get_or_404(session, owner_id=current_user.id, order_id=order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="order not found")

    lines_by_oid = await repo.get_lines_by_order_ids(session, order_ids=[o.id])
    return await _build_order_read(
        session=session,
        owner_id=current_user.id,
        order=o,
        lines=lines_by_oid.get(o.id, []),
    )


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = OrdersService()

    data = payload.model_dump(mode="json", by_alias=True)
    decor_prices = data.get("decorPrices")

    if payload.decor_prices is not None:
        data = payload.model_dump(mode="json", by_alias=True)

    extra = data.get("extra")
    if payload.extra is not None:
        extra = {
            "delivery": payload.extra.delivery,
            "urgency": payload.extra.urgency,
            "other": payload.extra.other,
            "discount": payload.extra.discount,
        }

    references = data.get("references")
    if payload.references is not None:
        references = [{"uri": r.uri} for r in payload.references]

    order = Order(
        owner_id=current_user.id,
        name=payload.name,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        order_platform=payload.order_platform,
        delivery_type=OrderDeliveryType(payload.delivery_type),
        address=payload.address,
        date=_parse_date(payload.date),
        time=_parse_time(payload.time),
        notes=payload.notes,
        decor_prices=decor_prices,
        extra=extra,
        references=references,
        status=OrderStatus(payload.status),
        paid_amount=payload.paid_amount,
        in_planner=payload.in_planner,
    )

    items = []
    for p in payload.products:
        items.append(
            {
                "product_id": p.product_id,
                "amount": p.amount,
                "filling_id": p.filling_id,
            }
        )

    try:
        lines = await svc.build_lines_from_input(session, owner_id=current_user.id, items=items)
        created = await svc.create(session, owner_id=current_user.id, order=order, lines=lines)
    except ProductNotFoundInOrderError:
        raise HTTPException(status_code=404, detail="one of products not found")
    except InvalidFillingError:
        raise HTTPException(status_code=400, detail="invalid fillingId for selected product")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repo = OrdersRepository()
    lines_by_oid = await repo.get_lines_by_order_ids(session, order_ids=[created.id])
    return await _build_order_read(
        session=session,
        owner_id=current_user.id,
        order=created,
        lines=lines_by_oid.get(created.id, []),
    )


@router.put("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = OrdersService()

    data = payload.model_dump(mode="json", by_alias=True)

    decor_prices = data.get("decorPrices")
    if payload.decor_prices is not None:
        decor_prices = [d.model_dump(mode="json", by_alias=True) for d in payload.decor_prices]

    extra = data.get("extra")
    if payload.extra is not None:
        extra = payload.extra.model_dump(mode="json", by_alias=True)

    references = data.get("references")
    if payload.references is not None:
        references = [r.model_dump(mode="json", by_alias=True) for r in payload.references]

    patch = Order(
        owner_id=current_user.id,
        name=payload.name,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        order_platform=payload.order_platform,
        delivery_type=OrderDeliveryType(payload.delivery_type),
        address=payload.address,
        date=_parse_date(payload.date),
        time=_parse_time(payload.time),
        notes=payload.notes,
        decor_prices=decor_prices,
        extra=extra,
        references=references,
        status=OrderStatus(payload.status),
        paid_amount=payload.paid_amount,
        in_planner=payload.in_planner,
    )

    items = []
    for p in payload.products:
        items.append(
            {
                "product_id": p.product_id,
                "amount": p.amount,
                "filling_id": p.filling_id,
            }
        )

    try:
        lines = await svc.build_lines_from_input(session, owner_id=current_user.id, items=items)
        updated = await svc.update(session, owner_id=current_user.id, order_id=order_id, patch=patch, lines=lines)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="order not found")
    except ProductNotFoundInOrderError:
        raise HTTPException(status_code=404, detail="one of products not found")
    except InvalidFillingError:
        raise HTTPException(status_code=400, detail="invalid fillingId for selected product")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repo = OrdersRepository()
    lines_by_oid = await repo.get_lines_by_order_ids(session, order_ids=[updated.id])
    return await _build_order_read(
        session=session,
        owner_id=current_user.id,
        order=updated,
        lines=lines_by_oid.get(updated.id, []),
    )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    svc = OrdersService()
    try:
        await svc.delete(session, owner_id=current_user.id, order_id=order_id)
        return None
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="order not found")