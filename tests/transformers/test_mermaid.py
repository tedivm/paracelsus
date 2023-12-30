from paracelsus.transformers.mermaid import Mermaid


def test_mermaid(metaclass):
    mermaid = Mermaid(metaclass=metaclass)
    graph_string = str(mermaid)

    assert "users {" in graph_string
    assert "posts {" in graph_string
    assert "comments {" in graph_string

    assert "users ||--o{ posts : author" in graph_string
    assert "posts ||--o{ comments : post" in graph_string
    assert "users ||--o{ comments : author" in graph_string

    assert "CHAR(32) author FK" in graph_string
    assert 'CHAR(32) post FK "nullable"' in graph_string
    assert "DATETIME created" in graph_string
