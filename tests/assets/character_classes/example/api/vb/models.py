from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class VbModel(Base):
    __tablename__ = "vb_table"
    id = mapped_column(String, primary_key=True)
