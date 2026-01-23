from typing import Union
from sqlalchemy.schema import MetaData
from paracelsus.graph import compare_metadata


def mermaid_assert(
    actual: Union[str, MetaData],
    expected: Union[MetaData, None] = None,
    omit_comments: bool = False,
) -> None:
    """
    Asserts that a mermaid graph (string or MetaData) matches expected structure.

    This function supports two modes:
    1. Legacy mode: If actual is a string, performs basic string assertions (for backward compatibility)
    2. Dynamic mode: If actual is MetaData, compares it with expected MetaData
    """
    # Legacy mode: string comparison (for backward compatibility)
    if isinstance(actual, str):
        # Basic assertions for backward compatibility
        assert "users {" in actual
        assert "posts {" in actual
        assert "comments {" in actual

        assert "users ||--o{ posts : author" in actual
        assert "posts ||--o{ comments : post" in actual
        assert "users ||--o{ comments : author" in actual

        assert "CHAR(32) author FK" in actual
        assert 'CHAR(32) post FK "nullable"' in actual
        assert 'BOOLEAN live "True if post is published,nullable"' in actual
        assert "DATETIME created" in actual

        trailing_newline_assert(actual)

    # Dynamic mode: MetaData comparison
    else:
        if expected is None:
            raise ValueError("expected MetaData is required when actual is MetaData")
        compare_metadata(actual, expected, omit_comments=omit_comments)


def dot_assert(output: str) -> None:
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>users</b></td></tr>' in output
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>posts</b></td></tr>' in output
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>comments</b></td></tr>' in output

    # Check for edge relationships with flexible attribute ordering
    _assert_dot_edge(output, "users", "posts", "author", "crow", "none")
    _assert_dot_edge(output, "posts", "comments", "post", "crow", "none")
    _assert_dot_edge(output, "users", "comments", "author", "crow", "none")

    assert '<tr><td align="left">CHAR(32)</td><td align="left">author</td><td>Foreign Key</td></tr>' in output
    assert '<tr><td align="left">CHAR(32)</td><td align="left">post</td><td>Foreign Key</td></tr>' in output
    assert '<tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>' in output


def _assert_dot_edge(
    output: str,
    left_table: str,
    right_table: str,
    label: str,
    arrowhead: str,
    arrowtail: str,
) -> None:
    """Assert that a dot edge exists with the expected attributes, regardless of order."""
    import re

    # Match edge line with flexible whitespace and attribute ordering
    pattern = rf"{left_table}\s+--\s+{right_table}\s+\[(.*?)\];"
    match = re.search(pattern, output)

    assert match, f"Edge '{left_table} -- {right_table}' not found in output"

    attributes = match.group(1)

    # Check each required attribute is present
    assert f"label={label}" in attributes, f"label={label} not found in edge attributes: {attributes}"
    assert "dir=both" in attributes, f"dir=both not found in edge attributes: {attributes}"
    assert f"arrowhead={arrowhead}" in attributes, f"arrowhead={arrowhead} not found in edge attributes: {attributes}"
    assert f"arrowtail={arrowtail}" in attributes, f"arrowtail={arrowtail} not found in edge attributes: {attributes}"

    trailing_newline_assert(output)


def trailing_newline_assert(output: str) -> None:
    """
    Check that the output ends with a single newline.
    This reduces end user linter rewrites,
    e.g. from pre-commit's end-of-file-fixer hook.
    """
    assert output.endswith("\n")
    assert not output.endswith("\n\n")
