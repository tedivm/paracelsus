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

    trailing_newline_assert(output)


def dot_assert(output: str) -> None:
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>users</b></td></tr>' in output
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>posts</b></td></tr>' in output
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>comments</b></td></tr>' in output

    assert "users -- posts [label=author, dir=both, arrowhead=crow, arrowtail=none];" in output
    assert "posts -- comments [label=post, dir=both, arrowhead=crow, arrowtail=none];" in output
    assert "users -- comments [label=author, dir=both, arrowhead=crow, arrowtail=none];" in output

    assert '<tr><td align="left">CHAR(32)</td><td align="left">author</td><td>Foreign Key</td></tr>' in output
    assert '<tr><td align="left">CHAR(32)</td><td align="left">post</td><td>Foreign Key</td></tr>' in output
    assert '<tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>' in output

    trailing_newline_assert(output)


def trailing_newline_assert(output: str) -> None:
    """
    Check that the output ends with a single newline.
    This reduces end user linter rewrites,
    e.g. from pre-commit's end-of-file-fixer hook.
    """
    assert output.endswith("\n")
    assert not output.endswith("\n\n")
