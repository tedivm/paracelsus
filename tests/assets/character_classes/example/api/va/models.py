from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class VaModel(Base):
    __tablename__ = "va_table"
    id = mapped_column(String, primary_key=True)
