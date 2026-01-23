from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ..base import Base


class BarModel(Base):
    __tablename__ = "bar_table"
    id = mapped_column(String, primary_key=True)
