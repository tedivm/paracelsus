from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ...base import Base


class User(Base):
    __tablename__ = "users"
    id = mapped_column(String, primary_key=True)
