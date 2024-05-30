import pytest
from paracelsus.graph import get_graph_string

from .utils import mermaid_assert


def test_get_graph_string(package_path):
    graph_string = get_graph_string("example.base:Base", ["example.models"], set(), set(), [package_path], "mermaid")
    mermaid_assert(graph_string)


def test_get_graph_string_with_exclude(package_path):
    """Excluding tables removes them from the graph string."""
    graph_string = get_graph_string(
        "example.base:Base", ["example.models"], set(), {"comments"}, [package_path], "mermaid"
    )
    assert "comments {" not in graph_string
    assert "posts {" in graph_string
    assert "users {" in graph_string

    # Excluding a table to which another table holds a foreign key will raise an error.
    with pytest.raises(RuntimeError):
        get_graph_string("example.base:Base", ["example.models"], set(), {"users"}, [package_path], "mermaid")


def test_get_graph_string_with_include(package_path):
    """Excluding tables keeps them in the graph string."""
    graph_string = get_graph_string(
        "example.base:Base", ["example.models"], {"users"}, set(), [package_path], "mermaid"
    )
    assert "comments {" not in graph_string
    assert "posts {" not in graph_string
    assert "users {" in graph_string

    # Including a table that holds a foreign key to a non-existing table will raise an error.
    with pytest.raises(RuntimeError):
        get_graph_string("example.base:Base", ["example.models"], {"posts"}, set(), [package_path], "mermaid")
