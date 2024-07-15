from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, inspect, select

from server.db import get_db


async def upsert_one(db_model: SQLModel, session=get_db()):
    async with session as db:
        print(f"DEBUG >>> Session ID (upsert_one): {id(db)}")

        # Determine what the primary key-value pair is for this item.
        model_class = db_model.__class__
        print(f"\nDEBUG >>>  {db_model=} {model_class=}")
        mapper = inspect(model_class)
        primary_key_column = mapper.primary_key[0].name
        primary_key_value = getattr(db_model, primary_key_column)
        print(f"DEBUG >>> {primary_key_column=}, {primary_key_value=}")

        # Check if the table exists
        print(f"DEBUG >>> TABLES: {SQLModel.metadata.tables.keys()}")

        # Check if the item already exists based on the primary key
        statement = select(model_class).where(
            getattr(model_class, primary_key_column) == primary_key_value
        )

        from sqlalchemy.exc import OperationalError

        try:
            result = await db.execute(statement)
        except OperationalError:
            print("DEBUG >>> Yes, Virginia, it is in fact as crazy as you believe.")
            raise

        existing_item = result.scalar_one_or_none()
        print("DEBUG >>> the select statement worked")

        if existing_item:
            # If it exists, update the existing item
            for key, value in db_model.model_dump().items():
                setattr(existing_item, key, value)
            db.add(existing_item)
        else:
            print("DEBUG >>> This is an INSERT (create) action.")
            # If it doesn't exist, insert the new item
            db.add(db_model)

        await db.commit()
