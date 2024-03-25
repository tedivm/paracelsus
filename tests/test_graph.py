from paracelsus.graph import get_graph_string


def test_get_graph_string(package_path):
    graph_string = get_graph_string("example.base:Base", ["example.models"], [package_path], "mermaid")

    assert "users {" in graph_string
    assert "posts {" in graph_string
    assert "comments {" in graph_string

    assert "users ||--o{ posts : author" in graph_string
    assert "posts ||--o{ comments : post" in graph_string
    assert "users ||--o{ comments : author" in graph_string

    assert "CHAR(32) author FK" in graph_string
    assert 'CHAR(32) post FK "nullable"' in graph_string
    assert "DATETIME created" in graph_string
