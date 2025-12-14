import sqlalchemy
from sqlalchemy import Column, Enum, MetaData, Table

from paracelsus.config import Layouts
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
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based", max_enum_members=10)
    status_column = table.columns["status"]
    column_str = mermaid._column(status_column)

    assert "values: draft, published, archived" in column_str


def test_mermaid_enum_values_hidden_when_max_zero():
    metadata = MetaData()
    status_enum = Enum("draft", "published", "archived", name="status_enum")
    table = Table(
        "post",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("status", status_enum, nullable=True),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based", max_enum_members=0, layout=None)
    status_column = table.columns["status"]
    column_str = mermaid._column(status_column)

    assert "values:" not in column_str
    assert "ENUM status" in column_str


def test_mermaid_enum_values_limited():
    metadata = MetaData()
    status_enum = Enum("draft", "published", "archived", "deleted", "review", name="status_enum")
    table = Table(
        "post",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("status", status_enum, nullable=True),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based", max_enum_members=3, layout=None)
    status_column = table.columns["status"]
    column_str = mermaid._column(status_column)

    assert "values: draft, published, ..., review" in column_str
    assert "archived" not in column_str
    assert "deleted" not in column_str


def test_mermaid_with_no_layout(metaclass, mermaid_full_string_with_no_layout):
    mermaid = Mermaid(metaclass=metaclass, column_sort="preserve-order", layout=None)
    assert str(mermaid) == mermaid_full_string_with_no_layout


def test_mermaid_with_dagre_layout(metaclass, mermaid_full_string_with_dagre_layout):
    mermaid = Mermaid(metaclass=metaclass, column_sort="preserve-order", layout=Layouts.dagre)
    assert str(mermaid) == mermaid_full_string_with_dagre_layout


def test_mermaid_with_elk_layout(metaclass, mermaid_full_string_with_elk_layout):
    mermaid = Mermaid(metaclass=metaclass, column_sort="preserve-order", layout=Layouts.elk)
    assert str(mermaid) == mermaid_full_string_with_elk_layout


def test_mermaid_numeric_type_with_parameters():
    """Test that NUMERIC types with parameters are sanitized correctly (issue #51)."""
    metadata = MetaData()
    table = Table(
        "product",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("price", sqlalchemy.Numeric(10, 2), nullable=False),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based")
    price_column = table.columns["price"]
    column_str = mermaid._column(price_column)

    # Should use hyphen instead of comma
    assert "NUMERIC(10-2)" in column_str
    assert "NUMERIC(10, 2)" not in column_str


def test_mermaid_decimal_type_with_parameters():
    """Test that DECIMAL types with parameters are sanitized correctly (issue #51)."""
    metadata = MetaData()
    table = Table(
        "account",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("balance", sqlalchemy.DECIMAL(8, 3), nullable=False),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based")
    balance_column = table.columns["balance"]
    column_str = mermaid._column(balance_column)

    # Should use hyphen instead of comma
    assert "DECIMAL(8-3)" in column_str
    assert "DECIMAL(8, 3)" not in column_str


def test_mermaid_types_without_parameters_unchanged():
    """Test that types without parameters are not affected by sanitization."""
    metadata = MetaData()
    table = Table(
        "user",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("name", sqlalchemy.String(100), nullable=False),
        Column("active", sqlalchemy.Boolean, nullable=False),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based")

    # String(100) has parentheses but no comma - should be unchanged
    name_column = table.columns["name"]
    name_str = mermaid._column(name_column)
    assert "VARCHAR(100)" in name_str or "STRING(100)" in name_str

    # Boolean has no parameters - should be unchanged
    active_column = table.columns["active"]
    active_str = mermaid._column(active_column)
    assert "BOOLEAN" in active_str or "BOOL" in active_str


def test_mermaid_custom_delimiter():
    """Test using a custom delimiter instead of hyphen."""
    metadata = MetaData()
    table = Table(
        "product",
        metadata,
        Column("id", sqlalchemy.Integer, primary_key=True),
        Column("price", sqlalchemy.Numeric(10, 2), nullable=False),
    )
    mermaid = Mermaid(metaclass=metadata, column_sort="key-based", type_parameter_delimiter="_")
    price_column = table.columns["price"]
    column_str = mermaid._column(price_column)

    # Should use underscore instead of comma
    assert "NUMERIC(10_2)" in column_str
    assert "NUMERIC(10-2)" not in column_str
    assert "NUMERIC(10, 2)" not in column_str


def test_mermaid_invalid_delimiter_with_comma():
    """Test that delimiter containing comma raises ValueError."""
    metadata = MetaData()
    try:
        Mermaid(metaclass=metadata, column_sort="key-based", type_parameter_delimiter=",")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot contain commas or spaces" in str(e)


def test_mermaid_invalid_delimiter_with_space():
    """Test that delimiter containing space raises ValueError."""
    metadata = MetaData()
    try:
        Mermaid(metaclass=metadata, column_sort="key-based", type_parameter_delimiter=" ")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot contain commas or spaces" in str(e)


def test_mermaid_invalid_delimiter_with_comma_and_space():
    """Test that delimiter containing comma and space raises ValueError."""
    metadata = MetaData()
    try:
        Mermaid(metaclass=metadata, column_sort="key-based", type_parameter_delimiter=", ")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot contain commas or spaces" in str(e)
