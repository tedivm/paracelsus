from uuid import UUID

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from paracelsus.transformers.utils import is_unique


class Base(DeclarativeBase):
    __table_args__ = {"schema": "some_schema"}


class Foo(Base):
    __tablename__ = "foo"
    id: Mapped[UUID] = mapped_column(primary_key=True)

    bar: Mapped[str] = mapped_column(unique=True)
    baz: Mapped[str] = mapped_column()

    beep: Mapped[str]
    boop: Mapped[str]

    __table_args__ = (
        UniqueConstraint("baz"),
        UniqueConstraint("beep", "boop"),
        Base.__table_args__,
    )


@pytest.mark.parametrize(
    "column_name, expected_unique",
    [
        ("id", True),  # primary key
        ("bar", True),  # unique=True
        ("baz", True),  # UniqueConstraint on single column
        ("beep", False),  # part of multi-column UniqueConstraint
        ("boop", False),  # part of multi-column UniqueConstraint
    ],
)
def test_is_unique(column_name: str, expected_unique: bool):
    column = Foo.__table__.columns[column_name]

    assert is_unique(column) == expected_unique
