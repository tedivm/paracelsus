from paracelsus.transformers.dot import Dot

from ..utils import dot_assert


def test_dot(metaclass):
    dot = Dot(metaclass=metaclass, column_sort="key-based")
    graph_string = str(dot)
    dot_assert(graph_string)


def test_dot_column_sort_preserve_order(metaclass):
    dot = Dot(metaclass=metaclass, column_sort="preserve-order")
    graph_string = str(dot)

    # Verify structure and relationships are correct
    dot_assert(graph_string)

    # Verify preserve-order specific column ordering
    # In preserve-order mode, columns should appear in the order they're defined
    # users: id, display_name, created
    assert graph_string.index("users") < graph_string.index("id")
    assert graph_string.index("id") < graph_string.index("display_name")
    assert graph_string.index("display_name") < graph_string.index("created")
