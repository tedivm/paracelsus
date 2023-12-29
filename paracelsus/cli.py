import importlib
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


@app.command()
def graph(
    base_class_path: Annotated[str, typer.Argument(help="The SQLAlchemy base class used by the database to graph.")],
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
    # Update the PYTHON_PATH to allow more module imports.
    for dir in python_dir:
        sys.path.append(dir)

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
    if format.value not in transformers:
        raise ValueError(f"Unknown Format: {format.value}")
    transformer = transformers[format.value]

    # Save the graph structure to string.
    graph_output = str(transformer(metadata))

    #
    typer.echo(graph_output)


@app.command()
def version():
    from . import _version

    typer.echo(_version.version)


if __name__ == "__main__":
    app()
