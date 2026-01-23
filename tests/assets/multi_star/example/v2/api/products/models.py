from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ....base import Base


class V2Product(Base):
    __tablename__ = "v2_products"
    id = mapped_column(String, primary_key=True)
