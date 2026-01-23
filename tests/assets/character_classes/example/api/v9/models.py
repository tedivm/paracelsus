from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class V9Model(Base):
    __tablename__ = "v9_table"
    id = mapped_column(String, primary_key=True)
