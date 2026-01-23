from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class Product(Base):
    __tablename__ = "products"
    id = mapped_column(String, primary_key=True)
