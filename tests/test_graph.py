from paracelsus.graph import get_graph_string

from .utils import mermaid_assert


def test_get_graph_string(package_path):
    graph_string = get_graph_string("example.base:Base", ["example.models"], [package_path], "mermaid")
    mermaid_assert(graph_string)
