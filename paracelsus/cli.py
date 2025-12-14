import re
import sys
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

import typer
from typing_extensions import Annotated

from paracelsus.config import (
    MAX_ENUM_MEMBERS_DEFAULT,
    SORT_DEFAULT,
    ColumnSorts,
    Formats,
    Layouts,
    ParacelsusSettingsForGraph,
    ParacelsusSettingsForInject,
)

from .graph import get_graph_string, transformers
from .pyproject import get_pyproject_settings

app = typer.Typer()


def get_base_class(base_class_path: str | None, base_from_config: str) -> str:
    if base_class_path:
        return base_class_path
    if base_from_config:
        return base_from_config

    raise ValueError(
        dedent(
            """\
        Either provide `--base-class-path` argument or define `base` in the pyproject.toml file:
            [tool.paracelsus]
            base = "example.base:Base"
        """
        )
    )


@app.command(help="Create the graph structure and print it to stdout.")
def graph(
    config: Annotated[
        Path,
        typer.Option(
            help="Path to a pyproject.toml file to load configuration from.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            exists=True,
            default_factory=lambda: Path.cwd() / "pyproject.toml",
            show_default=str(Path.cwd() / "pyproject.toml"),
        ),
    ],
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
        Optional[ColumnSorts],
        typer.Option(
            help="Specifies the method of sorting columns in diagrams.",
            show_default=str(SORT_DEFAULT.value),
        ),
    ] = None,
    omit_comments: Annotated[
        Optional[bool],
        typer.Option(
            "--omit-comments",
            help="Omit SQLAlchemy column comments from the diagram.",
        ),
    ] = None,
    max_enum_members: Annotated[
        Optional[int],
        typer.Option(
            "--max-enum-members",
            help="Maximum number of enum members to display in diagrams. 0 means no enum values are shown, any positive number limits the display.",
            show_default=str(MAX_ENUM_MEMBERS_DEFAULT),
        ),
    ] = None,
    layout: Annotated[
        Optional[Layouts],
        typer.Option(
            help="Specifies the layout of the diagram. Only applicable for mermaid format.",
        ),
    ] = None,
    type_parameter_delimiter: Annotated[
        Optional[str],
        typer.Option(
            "--type-parameter-delimiter",
            help="Delimiter to use for type parameters in mermaid diagrams (e.g., NUMERIC(10-2)). Cannot contain commas or spaces.",
            show_default="-",
        ),
    ] = None,
):
    settings = get_pyproject_settings(config_file=config)

    graph_settings = ParacelsusSettingsForGraph(
        base_class_path=get_base_class(base_class_path, settings.base),
        import_module=import_module + settings.imports,
        include_tables=set(include_tables + settings.include_tables),
        exclude_tables=set(exclude_tables + settings.exclude_tables),
        python_dir=python_dir,
        format=format,
        column_sort=column_sort if column_sort is not None else settings.column_sort,
        omit_comments=omit_comments if omit_comments is not None else settings.omit_comments,
        max_enum_members=max_enum_members if max_enum_members is not None else settings.max_enum_members,
        layout=layout,
        type_parameter_delimiter=type_parameter_delimiter
        if type_parameter_delimiter is not None
        else settings.type_parameter_delimiter,
    )

    graph_string = get_graph_string(
        **asdict(graph_settings),
    )
    typer.echo(graph_string, nl=not graph_string.endswith("\n"))


@app.command(help="Create a graph and inject it as a code field into a markdown file.")
def inject(
    config: Annotated[
        Path,
        typer.Option(
            help="Path to a pyproject.toml file to load configuration from.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            exists=True,
            default_factory=lambda: Path.cwd() / "pyproject.toml",
            show_default=str(Path.cwd() / "pyproject.toml"),
        ),
    ],
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
        Optional[str],
        typer.Argument(help="The SQLAlchemy base class used by the database to graph."),
    ] = None,
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
        Optional[ColumnSorts],
        typer.Option(
            help="Specifies the method of sorting columns in diagrams.",
            show_default=str(SORT_DEFAULT.value),
        ),
    ] = None,
    omit_comments: Annotated[
        Optional[bool],
        typer.Option(
            "--omit-comments",
            help="Omit SQLAlchemy column comments from the diagram.",
        ),
    ] = None,
    max_enum_members: Annotated[
        Optional[int],
        typer.Option(
            "--max-enum-members",
            help="Maximum number of enum members to display in diagrams. 0 means no enum values are shown, any positive number limits the display.",
            show_default=str(MAX_ENUM_MEMBERS_DEFAULT),
        ),
    ] = None,
    layout: Annotated[
        Optional[Layouts],
        typer.Option(
            help="Specifies the layout of the diagram. Only applicable for mermaid format.",
        ),
    ] = None,
    type_parameter_delimiter: Annotated[
        Optional[str],
        typer.Option(
            "--type-parameter-delimiter",
            help="Delimiter to use for type parameters in mermaid diagrams (e.g., NUMERIC(10-2)). Cannot contain commas or spaces.",
            show_default="-",
        ),
    ] = None,
):
    settings = get_pyproject_settings(config_file=config)

    inject_settings = ParacelsusSettingsForInject(
        graph_settings=ParacelsusSettingsForGraph(
            base_class_path=get_base_class(base_class_path, settings.base),
            import_module=import_module + settings.imports,
            include_tables=set(include_tables + settings.include_tables),
            exclude_tables=set(exclude_tables + settings.exclude_tables),
            python_dir=python_dir,
            format=format,
            column_sort=column_sort if column_sort is not None else settings.column_sort,
            omit_comments=omit_comments if omit_comments is not None else settings.omit_comments,
            max_enum_members=max_enum_members if max_enum_members is not None else settings.max_enum_members,
            layout=layout,
            type_parameter_delimiter=type_parameter_delimiter
            if type_parameter_delimiter is not None
            else settings.type_parameter_delimiter,
        ),
        file=file,
        replace_begin_tag=replace_begin_tag,
        replace_end_tag=replace_end_tag,
        check=check,
    )

    # Generate Graph
    graph = get_graph_string(
        **asdict(inject_settings.graph_settings),
    )

    comment_format = transformers[inject_settings.graph_settings.format].comment_format  # type: ignore

    # Convert Graph to Injection String
    graph_piece = f"""{inject_settings.replace_begin_tag}
```{comment_format}
{graph}
```
{inject_settings.replace_end_tag}"""

    # Get content from current file.
    old_content = inject_settings.file.read_text()

    # Replace old content with newly generated content.
    pattern = re.escape(inject_settings.replace_begin_tag) + "(.*)" + re.escape(inject_settings.replace_end_tag)
    new_content = re.sub(pattern, graph_piece, old_content, flags=re.MULTILINE | re.DOTALL)

    # Return result depends on whether we're in check mode.
    if inject_settings.check:
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
        inject_settings.file.write_text(new_content)


@app.command(help="Display the current installed version of paracelsus.")
def version():
    from . import _version

    typer.echo(_version.version)


if __name__ == "__main__":
    app()
