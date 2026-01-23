from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ..base import Base


class SubpackageBModel(Base):
    __tablename__ = "subpackage_b_table"
    id = mapped_column(String, primary_key=True)
