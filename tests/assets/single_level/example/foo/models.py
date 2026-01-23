from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ..base import Base


class FooModel(Base):
    __tablename__ = "foo_table"
    id = mapped_column(String, primary_key=True)
