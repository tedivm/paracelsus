def mermaid_assert(output: str) -> None:
    assert "users {" in output
    assert "posts {" in output
    assert "comments {" in output

    assert "users ||--o{ posts : author" in output
    assert "posts ||--o{ comments : post" in output
    assert "users ||--o{ comments : author" in output

    assert "CHAR(32) author FK" in output
    assert 'CHAR(32) post FK "nullable"' in output
    assert 'BOOLEAN live "True if post is published,nullable"' in output
    assert "DATETIME created" in output
