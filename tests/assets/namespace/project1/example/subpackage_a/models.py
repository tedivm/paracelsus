from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ..base import Base


class SubpackageAModel(Base):
    __tablename__ = "subpackage_a_table"
    id = mapped_column(String, primary_key=True)
