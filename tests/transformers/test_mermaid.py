import sqlalchemy
from sqlalchemy import Column, Enum, MetaData, Table

from paracelsus.transformers.mermaid import Mermaid

from ..utils import mermaid_assert


def test_mermaid(metaclass):
    mermaid = Mermaid(metaclass=metaclass, column_sort="key-based")
    graph_string = str(mermaid)
    mermaid_assert(graph_string)


def test_mermaid_column_sort_preserve_order(metaclass, mermaid_full_string_preseve_column_sort):
    mermaid = Mermaid(metaclass=metaclass, column_sort="preserve-order")
    assert str(mermaid) == mermaid_full_string_preseve_column_sort


def test_mermaid_keep_comments(metaclass):
    mermaid = Mermaid(metaclass=metaclass, column_sort="key-based", omit_comments=False)
    assert "True if post is published" in str(mermaid)


def test_mermaid_omit_comments(metaclass):
    mermaid = Mermaid(metaclass=metaclass, column_sort="key-based", omit_comments=True)
    assert "True if post is published" not in str(mermaid)


def test_mermaid_enum_values_present():
    metadata = MetaData()
    status_enum = Enum("draft", "published", "archived", name="status_enum")
    table = Table(
        "post",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("status", status_enum, nullable=True),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based")
    status_column = table.columns["status"]
    column_str = mermaid._column(status_column)

    assert "values: draft, published, archived" in column_str
