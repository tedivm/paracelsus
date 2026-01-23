from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from ....base import Base


class V1User(Base):
    __tablename__ = "v1_users"
    id = mapped_column(String, primary_key=True)
