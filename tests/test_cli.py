from pathlib import Path
from typing import Literal
import pytest

from typer.testing import CliRunner

from paracelsus.cli import app

from .utils import mermaid_assert

runner = CliRunner()


def test_graph(package_path: Path):
    result = runner.invoke(
        app,
        ["graph", "example.base:Base", "--import-module", "example.models", "--python-dir", str(package_path)],
    )

    assert result.exit_code == 0
    mermaid_assert(result.stdout)


@pytest.mark.parametrize("column_sort_arg", ["key-based", "preserve-order"])
def test_graph_column_sort(package_path: Path, column_sort_arg: Literal["key-based"] | Literal["preserve-order"]):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--column-sort",
            column_sort_arg,
        ],
    )

    assert result.exit_code == 0
    mermaid_assert(result.stdout)


def test_graph_with_exclusion(package_path: Path):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--exclude-tables",
            "comments",
        ],
    )
    assert result.exit_code == 0
    assert "posts {" in result.stdout
    assert "comments {" not in result.stdout


def test_graph_with_inclusion(package_path: Path):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--include-tables",
            "comments",
        ],
    )
    assert result.exit_code == 0
    assert "posts {" not in result.stdout
    assert "comments {" in result.stdout


def test_inject_check(package_path: Path):
    result = runner.invoke(
        app,
        [
            "inject",
            str(package_path / "README.md"),
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--check",
        ],
    )
    assert result.exit_code == 1


def test_inject(package_path: Path):
    result = runner.invoke(
        app,
        [
            "inject",
            str(package_path / "README.md"),
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
        ],
    )
    assert result.exit_code == 0

    with open(package_path / "README.md") as fp:
        readme = fp.read()
        mermaid_assert(readme)


@pytest.mark.parametrize("column_sort_arg", ["key-based", "preserve-order"])
def test_inject_column_sort(package_path: Path, column_sort_arg: Literal["key-based"] | Literal["preserve-order"]):
    result = runner.invoke(
        app,
        [
            "inject",
            str(package_path / "README.md"),
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--column-sort",
            column_sort_arg,
        ],
    )
    assert result.exit_code == 0

    with open(package_path / "README.md") as fp:
        readme = fp.read()
        mermaid_assert(readme)


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0


def test_graph_with_inclusion_regex(package_path: Path):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--include-tables",
            "^com.*",
        ],
    )
    assert result.exit_code == 0
    assert "comments {" in result.stdout
    assert "users {" not in result.stdout
    assert "post{" not in result.stdout


def test_graph_with_exclusion_regex(package_path: Path):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--exclude-tables",
            "^pos*.",
        ],
    )
    assert result.exit_code == 0
    assert "comments {" in result.stdout
    assert "users {" in result.stdout
    assert "post {" not in result.stdout


@pytest.mark.parametrize("layout_arg", ["dagre", "elk"])
def test_graph_layout(package_path: Path, layout_arg: Literal["dagre", "elk"]):
    result = runner.invoke(
        app,
        [
            "graph",
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--layout",
            layout_arg,
        ],
    )

    assert result.exit_code == 0
    mermaid_assert(result.stdout)


@pytest.mark.parametrize("layout_arg", ["dagre", "elk"])
def test_inject_layout(package_path: Path, layout_arg: Literal["dagre", "elk"]):
    result = runner.invoke(
        app,
        [
            "inject",
            str(package_path / "README.md"),
            "example.base:Base",
            "--import-module",
            "example.models",
            "--python-dir",
            str(package_path),
            "--layout",
            layout_arg,
        ],
    )
    assert result.exit_code == 0

    with open(package_path / "README.md") as fp:
        readme = fp.read()
        mermaid_assert(readme)
