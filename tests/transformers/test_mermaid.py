from paracelsus.transformers.mermaid import Mermaid

from ..utils import mermaid_assert


def test_mermaid(metaclass):
    mermaid = Mermaid(metaclass=metaclass)
    graph_string = str(mermaid)
    mermaid_assert(graph_string)
