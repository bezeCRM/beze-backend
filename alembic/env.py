import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.settings import settings
from app.modules.users.models import User  # noqa: F401
from app.modules.auth.models import RefreshToken  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401

# products related models must be imported so sqlmodel.metadata includes them for autogenerate
from app.modules.products.models import (  # noqa: F401
    Product,
    ProductPhoto,
)
from app.modules.orders.models import Order, OrderLine  # noqa: F401
from app.modules.planner.models import PlannerTask  # noqa: F401
from app.modules.profile.models import ProfileSettings # noqa: F401
from app.modules.auth.models import RefreshToken, PasswordResetToken  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.POSTGRES_DSN)

target_metadata = SQLModel.metadata


def do_run_migrations(connection):
    context.configure(
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema=target_metadata.schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = create_async_engine(settings.POSTGRES_DSN, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


asyncio.run(run_migrations_online())