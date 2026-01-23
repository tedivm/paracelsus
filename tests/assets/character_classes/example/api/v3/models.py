from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class V3Model(Base):
    __tablename__ = "v3_table"
    id = mapped_column(String, primary_key=True)
