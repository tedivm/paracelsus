from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ....base import Base


class SomethingAPIResource(Base):
    __tablename__ = "something_api_resources"
    id = mapped_column(String, primary_key=True)
