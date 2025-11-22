"""Contains example SQLAlchemy models demonstrating various cardinality relationships."""

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    __table_args__ = {"schema": "some_schema"}


class Bar(Base):
    __tablename__ = "bar"

    id: Mapped[UUID] = mapped_column(primary_key=True)


class Baz(Base):
    __tablename__ = "baz"

    id: Mapped[UUID] = mapped_column(primary_key=True)


class Beep(Base):
    __tablename__ = "beep"

    id: Mapped[UUID] = mapped_column(primary_key=True)


class Foo(Base):
    __tablename__ = "foo"
    id: Mapped[UUID] = mapped_column(primary_key=True)

    bar_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey(Bar.id), unique=True)

    baz_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey(Baz.id))

    beep_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey(Beep.id))
    boop: Mapped[str]

    __table_args__ = (
        UniqueConstraint(
            "baz_id",
        ),
        UniqueConstraint("beep_id", "boop"),
        Base.__table_args__,
    )
