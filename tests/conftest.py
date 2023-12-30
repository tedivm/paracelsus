from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import declarative_base, mapped_column


@pytest.fixture
def metaclass():
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        display_name = mapped_column(String(100))
        created = mapped_column(DateTime, nullable=False, default=datetime.utcnow())

    class Post(Base):
        __tablename__ = "posts"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        author = mapped_column(ForeignKey(User.id), nullable=False)
        created = mapped_column(DateTime, nullable=False, default=datetime.utcnow())
        live = mapped_column(Boolean, default=False)
        content = mapped_column(Text, default="")

    class Comment(Base):
        __tablename__ = "comments"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        post = mapped_column(Uuid, ForeignKey(Post.id), default=uuid4())
        author = mapped_column(ForeignKey(User.id), nullable=False)
        created = mapped_column(DateTime, nullable=False, default=datetime.utcnow())
        live = mapped_column(Boolean, default=False)
        content = mapped_column(Text, default="")

    return Base.metadata
