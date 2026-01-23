from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ......base import Base


class DeepAPIResource(Base):
    __tablename__ = "deep_api_resources"
    id = mapped_column(String, primary_key=True)
