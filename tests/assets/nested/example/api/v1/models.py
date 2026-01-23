from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class APIResource(Base):
    __tablename__ = "api_resources"
    id = mapped_column(String, primary_key=True)
