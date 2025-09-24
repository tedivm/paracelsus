import pytest
import textwrap


@pytest.fixture()
def mermaid_full_string_with_no_layout(mermaid_full_string_preseve_column_sort: str) -> str:
    return mermaid_full_string_preseve_column_sort


@pytest.fixture()
def mermaid_full_string_with_dagre_layout(mermaid_full_string_preseve_column_sort: str) -> str:
    front_matter = textwrap.dedent(
        """
        ---
            config:
                layout: dagre
        ---
        """
    )
    return f"{front_matter}{mermaid_full_string_preseve_column_sort}"


@pytest.fixture()
def mermaid_full_string_with_elk_layout(mermaid_full_string_preseve_column_sort: str) -> str:
    front_matter = textwrap.dedent(
        """
        ---
            config:
                layout: elk
        ---
        """
    )
    return f"{front_matter}{mermaid_full_string_preseve_column_sort}"
