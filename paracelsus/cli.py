import importlib
import os
import sys
from pathlib import Path
from pprint import pprint

import typer
from alembic.config import Config
from alembic.script import ScriptDirectory
from typing_extensions import Annotated

from .transformers.mermaid import Mermaid

app = typer.Typer()


def get_module(mymodule_path: Path):
    loader = importlib.machinery.SourceFileLoader("diagram_module", str(mymodule_path))
    spec = importlib.util.spec_from_loader("diagram_module", loader)
    diagram_module = importlib.util.module_from_spec(spec)
    loader.exec_module(diagram_module)
    return diagram_module


@app.command()
def test(
    working_dir: Annotated[
        Path, typer.Argument(file_okay=False, dir_okay=True, resolve_path=True, exists=True)
    ] = os.getcwd()
):
    typer.echo(working_dir)
    sys.path.append(working_dir)
    os.chdir(working_dir)
    typer.echo(sys.path)

    conf_path = working_dir / "alembic.ini"

    if not conf_path.exists():
        raise ValueError("Conf path doesn't exist")

    alembic_cfg = Config(conf_path)
    script = ScriptDirectory.from_config(alembic_cfg)
    env_path = working_dir / script.dir / "diagram.py"
    module = get_module(env_path)

    for name, table in module.target_metadata.tables.items():
        typer.echo(name)
        pprint(table.__dict__)
        typer.echo("\n")
        for column in table.columns:
            pprint(column.__dict__)
            typer.echo(f"\t{column.name} - {column.type}")
        typer.echo("\n")


@app.command()
def mermaid(
    working_dir: Annotated[
        Path, typer.Argument(file_okay=False, dir_okay=True, resolve_path=True, exists=True)
    ] = os.getcwd()
):
    sys.path.append(working_dir)
    os.chdir(working_dir)
    conf_path = working_dir / "alembic.ini"

    if not conf_path.exists():
        raise ValueError("Conf path doesn't exist")

    alembic_cfg = Config(conf_path)
    script = ScriptDirectory.from_config(alembic_cfg)
    env_path = working_dir / script.dir / "diagram.py"
    module = get_module(env_path)

    typer.echo(str(Mermaid(module.target_metadata)))


@app.command()
def version():
    from . import _version

    typer.echo(_version.version)


if __name__ == "__main__":
    app()
