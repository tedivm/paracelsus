from paracelsus.transformers.dot import Dot

from ..utils import dot_assert


def test_dot(metaclass):
    dot = Dot(metaclass=metaclass, column_sort="key-based")
    graph_string = str(dot)
    dot_assert(graph_string)


def test_dot_column_sort_preserve_order(metaclass, dot_full_string_preseve_column_sort):
    dot = Dot(metaclass=metaclass, column_sort="preserve-order")
    assert str(dot) == dot_full_string_preseve_column_sort
