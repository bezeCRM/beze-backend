from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_utils import to_camel
from app.modules.products.schemas import FillingItem, PhotoItem, ProductRead


OrderStatus = Literal["new", "inWork", "ready", "delivered", "canceled"]
OrderDeliveryType = Literal["pickup", "delivery"]
ProductUnit = Literal["piece", "kg"]


class OrderExtra(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    delivery: int = Field(ge=0, le=1000000000, default=0)
    urgency: int = Field(ge=0, le=1000000000, default=0)
    other: int = Field(ge=0, le=1000000000, default=0)
    discount: int = Field(ge=0, le=1000000000, default=0)


class OrderDecorPriceIn(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    product_id: UUID = Field(alias="productId")
    price: int = Field(ge=0, le=1000000000)


class OrderReferenceIn(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    uri: str = Field(min_length=1)


class OrderProductLineIn(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    product_id: UUID = Field(alias="productId")
    amount: float = Field(gt=0, le=1000000000)
    filling_id: UUID | None = Field(default=None, alias="fillingId")


class OrderCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None

    client_name: str = Field(alias="clientName", min_length=1, max_length=128)
    client_phone: str | None = Field(default=None, alias="clientPhone", max_length=32)
    order_platform: str | None = Field(default=None, alias="orderPlatform", max_length=128)

    delivery_type: OrderDeliveryType = Field(alias="deliveryType")
    address: str | None = None

    date: str
    time: str

    products: list[OrderProductLineIn]

    decor_prices: list[OrderDecorPriceIn] | None = Field(default=None, alias="decorPrices")
    extra: OrderExtra | None = None

    notes: str | None = Field(default=None, alias="notes", max_length=1024)
    references: list[OrderReferenceIn] | None = None

    status: OrderStatus
    paid_amount: int = Field(alias="paidAmount", ge=0)

    in_planner: bool = Field(alias="inPlanner")


class OrderUpdate(OrderCreate):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class OrderPatch(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None

    client_name: str | None = Field(default=None, alias="clientName", max_length=128)
    client_phone: str | None = Field(default=None, alias="clientPhone", max_length=32)
    order_platform: str | None = Field(default=None, alias="orderPlatform", max_length=128)

    delivery_type: OrderDeliveryType | None = Field(default=None, alias="deliveryType")
    address: str | None = None

    date: str | None = None
    time: str | None = None

    products: list[OrderProductLineIn] | None = None

    decor_prices: list[OrderDecorPriceIn] | None = Field(default=None, alias="decorPrices")
    extra: OrderExtra | None = None

    notes: str | None = None
    references: list[OrderReferenceIn] | None = None

    status: OrderStatus | None = None
    paid_amount: int | None = Field(default=None, alias="paidAmount", ge=0, le=1000000000)

    in_planner: bool | None = Field(default=None, alias="inPlanner")


class OrderDecorPriceRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    name: str | None = None
    price: int


class OrderProductLineRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    product: ProductRead
    amount: float
    filling: FillingItem | None = None
    price: int
    unit: ProductUnit


class OrderRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: UUID
    name: str | None = None

    client_name: str = Field(alias="clientName")
    client_phone: str | None = Field(default=None, alias="clientPhone")
    order_platform: str | None = Field(default=None, alias="orderPlatform")

    delivery_type: OrderDeliveryType = Field(alias="deliveryType")
    address: str | None = None

    date: str
    time: str

    products: list[OrderProductLineRead]

    decor_prices: list[OrderDecorPriceRead] | None = Field(default=None, alias="decorPrices")
    extra: OrderExtra | None = None

    notes: str | None = None
    references: list[PhotoItem] | None = None

    status: OrderStatus
    paid_amount: int = Field(alias="paidAmount")

    in_planner: bool = Field(alias="inPlanner")

    total_price: int = Field(alias="totalPrice")
    last_payment_at: datetime | None = Field(default=None, alias="lastPaymentAt")

    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")