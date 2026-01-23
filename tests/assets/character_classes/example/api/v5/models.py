from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class V5Model(Base):
    __tablename__ = "v5_table"
    id = mapped_column(String, primary_key=True)
