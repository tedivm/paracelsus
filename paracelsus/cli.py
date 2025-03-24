import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from typing_extensions import Annotated

from .graph import get_graph_string, transformers
from .pyproject import get_pyproject_settings

app = typer.Typer()

PYPROJECT_SETTINGS = get_pyproject_settings()


class Formats(str, Enum):
    mermaid = "mermaid"
    mmd = "mmd"
    dot = "dot"
    gv = "gv"


class ColumnSorts(str, Enum):
    key_based = "key-based"
    preserve = "preserve-order"


class Layouts(str, Enum):
    dagre = "dagre"
    elk = "elk"


if "column_sort" in PYPROJECT_SETTINGS:
    SORT_DEFAULT = ColumnSorts(PYPROJECT_SETTINGS["column_sort"]).value
else:
    SORT_DEFAULT = ColumnSorts.key_based.value

if "omit_comments" in PYPROJECT_SETTINGS:
    OMIT_COMMENTS_DEFAULT = PYPROJECT_SETTINGS["omit_comments"]
else:
    OMIT_COMMENTS_DEFAULT = False


def get_base_class(base_class_path: str | None, settings: Dict[str, Any] | None) -> str:
    if base_class_path:
        return base_class_path
    if not settings:
        raise ValueError("`base_class_path` argument must be passed if no pyproject.toml file is present.")
    if "base" not in settings:
        raise ValueError("`base_class_path` argument must be passed if not defined in pyproject.toml.")
    return settings["base"]


@app.command(help="Create the graph structure and print it to stdout.")
def graph(
    base_class_path: Annotated[
        Optional[str],
        typer.Argument(help="The SQLAlchemy base class used by the database to graph."),
    ] = None,
    import_module: Annotated[
        List[str],
        typer.Option(
            help="Module, typically an SQL Model, to import. Modules that end in :* will act as `from module import *`"
        ),
    ] = [],
    exclude_tables: Annotated[
        List[str],
        typer.Option(help="List of tables or regular expression patterns for tables that are excluded from the graph"),
    ] = [],
    include_tables: Annotated[
        List[str],
        typer.Option(help="List of tables or regular expression patterns for tables that are included in the graph"),
    ] = [],
    python_dir: Annotated[
        List[Path],
        typer.Option(
            help="Paths to add to the `PYTHON_PATH` for module lookup.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            exists=True,
        ),
    ] = [],
    format: Annotated[
        Formats, typer.Option(help="The file format to output the generated graph to.")
    ] = Formats.mermaid.value,  # type: ignore # Typer will fail to render the help message, but this code works.
    column_sort: Annotated[
        ColumnSorts,
        typer.Option(
            help="Specifies the method of sorting columns in diagrams.",
        ),
    ] = SORT_DEFAULT,  # type: ignore # Typer will fail to render the help message, but this code works.
    omit_comments: Annotated[
        bool,
        typer.Option(
            "--omit-comments",
            help="Omit SQLAlchemy column comments from the diagram.",
        ),
    ] = OMIT_COMMENTS_DEFAULT,
    layout: Annotated[
        Optional[Layouts],
        typer.Option(
            help="Specifies the layout of the diagram. Only applicable for mermaid format.",
        ),
    ] = None,
):
    settings = get_pyproject_settings()
    base_class = get_base_class(base_class_path, settings)

    if "imports" in settings:
        import_module.extend(settings["imports"])

    if layout and format != Formats.mermaid:
        raise ValueError("The `layout` parameter can only be used with the `mermaid` format.")

    graph_string = get_graph_string(
        base_class_path=base_class,
        import_module=import_module,
        include_tables=set(include_tables + settings.get("include_tables", [])),
        exclude_tables=set(exclude_tables + settings.get("exclude_tables", [])),
        python_dir=python_dir,
        format=format.value,
        column_sort=column_sort,
        omit_comments=omit_comments,
        layout=layout.value if layout else None,
    )
    typer.echo(graph_string, nl=not graph_string.endswith("\n"))


@app.command(help="Create a graph and inject it as a code field into a markdown file.")
def inject(
    file: Annotated[
        Path,
        typer.Argument(
            help="The file to inject the generated graph into.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            exists=True,
        ),
    ],
    base_class_path: Annotated[
        str,
        typer.Argument(help="The SQLAlchemy base class used by the database to graph."),
    ],
    replace_begin_tag: Annotated[
        str,
        typer.Option(help=""),
    ] = "<!-- BEGIN_SQLALCHEMY_DOCS -->",
    replace_end_tag: Annotated[
        str,
        typer.Option(help=""),
    ] = "<!-- END_SQLALCHEMY_DOCS -->",
    import_module: Annotated[
        List[str],
        typer.Option(
            help="Module, typically an SQL Model, to import. Modules that end in :* will act as `from module import *`"
        ),
    ] = [],
    exclude_tables: Annotated[
        List[str],
        typer.Option(help="List of tables that are excluded from the graph"),
    ] = [],
    include_tables: Annotated[
        List[str],
        typer.Option(help="List of tables that are included in the graph"),
    ] = [],
    python_dir: Annotated[
        List[Path],
        typer.Option(
            help="Paths to add to the `PYTHON_PATH` for module lookup.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            exists=True,
        ),
    ] = [],
    format: Annotated[
        Formats, typer.Option(help="The file format to output the generated graph to.")
    ] = Formats.mermaid.value,  # type: ignore # Typer will fail to render the help message, but this code works.
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Perform a dry run and return a success code of 0 if there are no changes or 1 otherwise.",
        ),
    ] = False,
    column_sort: Annotated[
        ColumnSorts,
        typer.Option(
            help="Specifies the method of sorting columns in diagrams.",
        ),
    ] = SORT_DEFAULT,  # type: ignore # Typer will fail to render the help message, but this code works.
    omit_comments: Annotated[
        bool,
        typer.Option(
            "--omit-comments",
            help="Omit SQLAlchemy column comments from the diagram.",
        ),
    ] = OMIT_COMMENTS_DEFAULT,
    layout: Annotated[
        Optional[Layouts],
        typer.Option(
            help="Specifies the layout of the diagram. Only applicable for mermaid format.",
        ),
    ] = None,
):
    settings = get_pyproject_settings()
    if "imports" in settings:
        import_module.extend(settings["imports"])

    if layout and format != Formats.mermaid:
        raise ValueError("The `layout` parameter can only be used with the `mermaid` format.")

    # Generate Graph
    graph = get_graph_string(
        base_class_path=base_class_path,
        import_module=import_module,
        include_tables=set(include_tables + settings.get("include_tables", [])),
        exclude_tables=set(exclude_tables + settings.get("exclude_tables", [])),
        python_dir=python_dir,
        format=format.value,
        column_sort=column_sort,
        omit_comments=omit_comments,
        layout=layout.value if layout else None,
    )

    comment_format = transformers[format].comment_format  # type: ignore

    # Convert Graph to Injection String
    graph_piece = f"""{replace_begin_tag}
```{comment_format}
{graph}
```
{replace_end_tag}"""

    # Get content from current file.
    with open(file, "r") as fp:
        old_content = fp.read()

    # Replace old content with newly generated content.
    pattern = re.escape(replace_begin_tag) + "(.*)" + re.escape(replace_end_tag)
    new_content = re.sub(pattern, graph_piece, old_content, flags=re.MULTILINE | re.DOTALL)

    # Return result depends on whether we're in check mode.
    if check:
        if new_content == old_content:
            # If content is the same then we passed the test.
            typer.echo("No changes detected.")
            sys.exit(0)
        else:
            # If content is different then we failed the test.
            typer.echo("Changes detected.")
            sys.exit(1)
    else:
        # Dump newly generated contents back to file.
        with open(file, "w") as fp:
            fp.write(new_content)


@app.command(help="Display the current installed version of paracelsus.")
def version():
    from . import _version

    typer.echo(_version.version)


if __name__ == "__main__":
    app()
