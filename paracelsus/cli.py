import importlib
import re
import sys
from enum import Enum
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated

from .transformers.dot import Dot
from .transformers.mermaid import Mermaid

app = typer.Typer()

transformers = {
    "mmd": Mermaid,
    "mermaid": Mermaid,
    "dot": Dot,
    "gv": Dot,
}


class Formats(str, Enum):
    mermaid = "mermaid"
    mmd = "mmd"
    dot = "dot"
    gv = "gv"


def get_graph_string(
    base_class_path: str,
    import_module: List[str],
    python_dir: List[Path],
    format: str,
) -> str:
    # Update the PYTHON_PATH to allow more module imports.
    for dir in python_dir:
        sys.path.append(str(dir))

    # Import the base class so the metadata class can be extracted from it.
    # The metadata class is passed to the transformer.
    module_path, class_name = base_class_path.split(":", 2)
    base_module = importlib.import_module(module_path)
    base_class = getattr(base_module, class_name)
    metadata = base_class.metadata

    # The modules holding the model classes have to be imported to get put in the metaclass model registry.
    # These modules aren't actually used in any way, so they are discarded.
    # They are also imported in scope of this function to prevent namespace pollution.
    for module in import_module:
        if ":*" in module:
            # Sure, execs are gross, but this is the only way to dynamically import wildcards.
            exec(f"from {module[:-2]} import *")
        else:
            importlib.import_module(module)

    # Grab a transformer.
    if format not in transformers:
        raise ValueError(f"Unknown Format: {format}")
    transformer = transformers[format]

    # Save the graph structure to string.
    return str(transformer(metadata))


@app.command(help="Create the graph structure and print it to stdout.")
def graph(
    base_class_path: Annotated[
        str,
        typer.Argument(help="The SQLAlchemy base class used by the database to graph."),
    ],
    import_module: Annotated[
        List[str],
        typer.Option(
            help="Module, typically an SQL Model, to import. Modules that end in :* will act as `from module import *`"
        ),
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
    ] = Formats.mermaid,
):
    typer.echo(
        get_graph_string(
            base_class_path=base_class_path,
            import_module=import_module,
            python_dir=python_dir,
            format=format.value,
        )
    )


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
    ] = Formats.mermaid,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Perform a dry run and return a success code of 0 if there are no changes or 1 otherwise.",
        ),
    ] = False,
):
    # Generate Graph
    graph = get_graph_string(
        base_class_path=base_class_path,
        import_module=import_module,
        python_dir=python_dir,
        format=format.value,
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
