import os
import shutil
import sys
import tempfile
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
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
def package_path() -> Generator[Path, None, None]:
    template_path = Path(os.path.dirname(os.path.realpath(__file__))) / "assets"
    with tempfile.TemporaryDirectory() as package_path:
        shutil.copytree(template_path, package_path, dirs_exist_ok=True)
        os.chdir(package_path)
        # RATIONALE: Purge cached 'example' modules so the new temp directory path is used for imports.
        # Without this, earlier tests leave sys.modules['example'] with a __path__ pointing at a deleted
        # temp directory. Later tests then fail to import submodules (e.g. example.cardinalities) because
        # Python reuses the stale package object and doesn't refresh its search path. Removing only these
        # entries enforces a clean import and prevents cross-test leakage / flakiness.
        for name in list(sys.modules.keys()):
            if name == "example" or name.startswith("example."):
                del sys.modules[name]
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


@pytest.fixture(name="expected_mermaid_smaller_graph")
def fixture_expected_mermaid_smaller_graph() -> str:
    return dedent("""\
        # Test Directory
    
        Please ignore.
        
        ## Schema
        
        <!-- BEGIN_SQLALCHEMY_DOCS -->
        ```mermaid
        
        ---
            config:
                layout: dagre
        ---
        erDiagram
          users {
            CHAR(32) id PK
            DATETIME created
            VARCHAR(100) display_name "nullable"
          }
        
          posts {
            CHAR(32) id PK
            CHAR(32) author FK
            TEXT content "nullable"
            DATETIME created
            BOOLEAN live "True if post is published,nullable"
          }
        
          users ||--o{ posts : author
        
        ```
        <!-- END_SQLALCHEMY_DOCS -->
    """)


@pytest.fixture(name="expected_mermaid_complete_graph")
def fixture_expected_mermaid_complete_graph() -> str:
    return dedent("""\
        # Test Directory
    
        Please ignore.
        
        ## Schema
        
        <!-- BEGIN_SQLALCHEMY_DOCS -->
        ```mermaid
        
        ---
            config:
                layout: dagre
        ---
        erDiagram
          users {
            CHAR(32) id PK
            DATETIME created
            VARCHAR(100) display_name "nullable"
          }
        
          posts {
            CHAR(32) id PK
            CHAR(32) author FK
            TEXT content "nullable"
            DATETIME created
            BOOLEAN live "True if post is published,nullable"
          }
        
          comments {
            CHAR(32) id PK
            CHAR(32) author FK
            CHAR(32) post FK "nullable"
            TEXT content "nullable"
            DATETIME created
            BOOLEAN live "nullable"
          }
        
          users ||--o{ posts : author
          posts ||--o{ comments : post
          users ||--o{ comments : author
        
        ```
        <!-- END_SQLALCHEMY_DOCS -->
    """)


@pytest.fixture(name="expected_mermaid_cardinalities_graph")
def fixture_expected_mermaid_cardinalities_graph() -> str:
    return dedent("""\
        # Test Directory
    
        Please ignore.
        
        ## Schema
        
        <!-- BEGIN_SQLALCHEMY_DOCS -->
        ```mermaid
        erDiagram
          bar {
            CHAR(32) id PK
          }

          baz {
            CHAR(32) id PK
          }

          beep {
            CHAR(32) id PK
          }

          foo {
            CHAR(32) id PK
            CHAR(32) bar_id FK
            CHAR(32) baz_id FK
            CHAR(32) beep_id FK
            VARCHAR boop
          }

          bar ||--o| foo : bar_id
          baz ||--o| foo : baz_id
          beep ||--o{ foo : beep_id

        ```
        <!-- END_SQLALCHEMY_DOCS -->
    """)
