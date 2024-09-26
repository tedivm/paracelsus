import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import declarative_base, mapped_column

UTC = timezone.utc


@pytest.fixture
def metaclass():
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        display_name = mapped_column(String(100))
        created = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))

    class Post(Base):
        __tablename__ = "posts"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        created = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
        author = mapped_column(ForeignKey(User.id), nullable=False)
        live = mapped_column(Boolean, default=False, comment="True if post is published")
        content = mapped_column(Text, default="")

    class Comment(Base):
        __tablename__ = "comments"

        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        created = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
        post = mapped_column(Uuid, ForeignKey(Post.id), default=uuid4())
        author = mapped_column(ForeignKey(User.id), nullable=False)
        live = mapped_column(Boolean, default=False)
        content = mapped_column(Text, default="")

    return Base.metadata


@pytest.fixture
def package_path():
    template_path = Path(os.path.dirname(os.path.realpath(__file__))) / "assets"
    with tempfile.TemporaryDirectory() as package_path:
        shutil.copytree(template_path, package_path, dirs_exist_ok=True)
        yield Path(package_path)


@pytest.fixture()
def mermaid_full_string_preseve_column_sort() -> str:
    return """erDiagram
  users {
    CHAR(32) id PK
    VARCHAR(100) display_name "nullable"
    DATETIME created
  }

  posts {
    CHAR(32) id PK
    DATETIME created
    CHAR(32) author FK
    BOOLEAN live "True if post is published,nullable"
    TEXT content "nullable"
  }

  comments {
    CHAR(32) id PK
    DATETIME created
    CHAR(32) post FK "nullable"
    CHAR(32) author FK
    BOOLEAN live "nullable"
    TEXT content "nullable"
  }

  users ||--o{ posts : author
  posts ||--o{ comments : post
  users ||--o{ comments : author
"""


@pytest.fixture()
def dot_full_string_preseve_column_sort() -> str:
    return """graph database {
users [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
        <tr><td colspan="3" bgcolor="lightblue"><b>users</b></td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">id</td><td>Primary Key</td></tr>
        <tr><td align="left">VARCHAR(100)</td><td align="left">display_name</td><td></td></tr>
        <tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>
    </table>
>, shape=none, margin=0];
posts [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
        <tr><td colspan="3" bgcolor="lightblue"><b>posts</b></td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">id</td><td>Primary Key</td></tr>
        <tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">author</td><td>Foreign Key</td></tr>
        <tr><td align="left">BOOLEAN</td><td align="left">live</td><td></td></tr>
        <tr><td align="left">TEXT</td><td align="left">content</td><td></td></tr>
    </table>
>, shape=none, margin=0];
users -- posts [label=author, dir=both, arrowhead=crow, arrowtail=none];
comments [label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
        <tr><td colspan="3" bgcolor="lightblue"><b>comments</b></td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">id</td><td>Primary Key</td></tr>
        <tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">post</td><td>Foreign Key</td></tr>
        <tr><td align="left">CHAR(32)</td><td align="left">author</td><td>Foreign Key</td></tr>
        <tr><td align="left">BOOLEAN</td><td align="left">live</td><td></td></tr>
        <tr><td align="left">TEXT</td><td align="left">content</td><td></td></tr>
    </table>
>, shape=none, margin=0];
posts -- comments [label=post, dir=both, arrowhead=crow, arrowtail=none];
users -- comments [label=author, dir=both, arrowhead=crow, arrowtail=none];
}
"""
