import pytest
import importlib
import sys
from pathlib import Path

from paracelsus.config import Layouts
from paracelsus.graph import get_graph_string, get_graph_metadata, compare_metadata
from paracelsus.finders import ModuleFinder
from paracelsus.models.pattern import Pattern
from paracelsus.graph import to_module_name

from .utils import mermaid_assert


@pytest.mark.parametrize("column_sort_arg", ["key-based", "preserve-order"])
def test_get_graph_string(column_sort_arg, package_path, metaclass):
    """Test get_graph_string with dynamic metadata comparison."""
    # Get actual metadata
    actual_metadata = get_graph_metadata(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[package_path],
    )

    # Compare with expected metadata from fixture
    mermaid_assert(actual_metadata, expected=metaclass)

    # Also test that serialization still works
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[package_path],
        format="mermaid",
        column_sort=column_sort_arg,
    )
    # Legacy string assertion for backward compatibility
    mermaid_assert(graph_string)


def test_get_graph_string_with_wildcard(single_level_package_path):
    """Test that wildcard patterns work correctly with dynamic metadata comparison."""
    actual_metadata = get_graph_metadata(
        base_class_path="example.base:Base",
        import_module=["example.*.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[single_level_package_path],
    )

    # Build expected metadata by manually importing all matching modules
    sys.path.insert(0, str(single_level_package_path))
    try:
        # Find all modules matching the pattern
        pattern = Pattern(mask="example.*.models")
        current_root = Path.cwd()
        finder = ModuleFinder(current_root, pattern.tokens)

        # Import all matching modules
        for file_path in finder.find():
            module_path = to_module_name(current_root, file_path)
            importlib.import_module(module_path)

        # Get expected metadata from base class
        base_module = importlib.import_module("example.base")
        base_class = getattr(base_module, "Base")
        expected_metadata = base_class.metadata

        # Compare metadata
        compare_metadata(actual_metadata, expected_metadata)
    finally:
        # Cleanup
        if str(single_level_package_path) in sys.path:
            sys.path.remove(str(single_level_package_path))
        # Clear imported modules
        for name in list(sys.modules.keys()):
            if name.startswith("example."):
                del sys.modules[name]


def test_get_graph_with_wildcard_mask_in_namespace_package(namespace_package_path):
    """Test namespace packages with wildcard patterns and merged metadata."""
    # Get actual metadata with namespace merging enabled
    actual_metadata = get_graph_metadata(
        base_class_path="project*.example.base:Base",
        import_module=["project*.example.*.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[namespace_package_path],
        merge_namespace_metadata=True,
    )

    # Verify that we have tables from both projects
    table_names = set(actual_metadata.tables.keys())
    # Should have tables from both project1 and project2
    assert "subpackage_a_table" in table_names or "project1_subpackage_a_table" in table_names
    assert "subpackage_b_table" in table_names or "project2_subpackage_b_table" in table_names

    # Verify the graph can be serialized
    from paracelsus.graph import serialize_metadata

    graph_string = serialize_metadata(
        actual_metadata,
        format="mermaid",
        column_sort="key-based",
    )
    assert "subpackage_a_table" in graph_string or "project1_subpackage_a_table" in graph_string
    assert "subpackage_b_table" in graph_string or "project2_subpackage_b_table" in graph_string


def test_get_graph_string_with_exclude(package_path):
    """Excluding tables removes them from the graph string."""
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables={"comments"},
        python_dir=[package_path],
        column_sort="key-based",
        format="mermaid",
    )
    assert "comments {" not in graph_string
    assert "posts {" in graph_string
    assert "users {" in graph_string
    assert "users ||--o{ posts" in graph_string

    # Excluding a table to which another table holds a foreign key will raise an error.
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables={"users", "comments"},
        python_dir=[package_path],
        format="mermaid",
        column_sort="key-based",
    )
    assert "posts {" in graph_string
    assert "users ||--o{ posts" not in graph_string


def test_get_graph_string_with_include(package_path):
    """Excluding tables keeps them in the graph string."""
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables={"users", "posts"},
        exclude_tables=set(),
        python_dir=[package_path],
        column_sort="key-based",
        format="mermaid",
    )
    assert "comments {" not in graph_string
    assert "posts {" in graph_string
    assert "users {" in graph_string
    assert "users ||--o{ posts" in graph_string

    # Including a table that holds a foreign key to a non-existing table will keep
    # the table but skip the connection.
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables={"posts"},
        exclude_tables=set(),
        python_dir=[package_path],
        column_sort="key-based",
        format="mermaid",
    )
    assert "posts {" in graph_string
    assert "users ||--o{ posts" not in graph_string


@pytest.mark.parametrize("layout_arg", ["dagre", "elk"])
def test_get_graph_string_with_layout(layout_arg, package_path, metaclass):
    """Test get_graph_string with layout using dynamic metadata comparison."""
    # Get actual metadata
    actual_metadata = get_graph_metadata(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[package_path],
    )

    # Compare with expected metadata
    mermaid_assert(actual_metadata, expected=metaclass)

    # Also test serialization with layout
    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[package_path],
        format="mermaid",
        column_sort="key-based",
        layout=Layouts(layout_arg),
    )
    # Legacy string assertion
    mermaid_assert(graph_string)


def test_get_graph_string_with_nested_glob_pattern(nested_package_path):
    """Integration test: get_graph_string with nested glob pattern."""

    graph_string = get_graph_string(
        base_class_path="example.base:Base",
        import_module=["example.*.*.models"],
        include_tables=set(),
        exclude_tables=set(),
        python_dir=[nested_package_path],
        format="mermaid",
        column_sort="key-based",
    )

    assert "users {" in graph_string or "products {" in graph_string or "api_resources {" in graph_string


def test_compare_metadata(metaclass):
    """Test compare_metadata function directly."""
    # Same metadata should compare successfully
    compare_metadata(metaclass, metaclass)

    # Different metadata should raise AssertionError
    from sqlalchemy.orm import declarative_base
    from sqlalchemy import String, Uuid
    from sqlalchemy.orm import mapped_column
    from uuid import uuid4

    Base2 = declarative_base()

    class DifferentTable(Base2):
        __tablename__ = "different_table"
        id = mapped_column(Uuid, primary_key=True, default=uuid4())
        name = mapped_column(String(100))

    different_metadata = Base2.metadata

    # Should raise AssertionError when comparing different metadata
    with pytest.raises(AssertionError):
        compare_metadata(metaclass, different_metadata)
