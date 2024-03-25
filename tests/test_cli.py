from typer.testing import CliRunner

from paracelsus.cli import app

runner = CliRunner()


def test_graph(package_path):
    result = runner.invoke(
        app, ["graph", "example.base:Base", "--import-module", "example.models", "--python-dir", str(package_path)]
    )

    assert result.exit_code == 0

    assert "users {" in result.stdout
    assert "posts {" in result.stdout
    assert "comments {" in result.stdout

    assert "users ||--o{ posts : author" in result.stdout
    assert "posts ||--o{ comments : post" in result.stdout
    assert "users ||--o{ comments : author" in result.stdout

    assert "CHAR(32) author FK" in result.stdout
    assert 'CHAR(32) post FK "nullable"' in result.stdout
    assert "DATETIME created" in result.stdout


def test_inject(package_path):
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


def test_version():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
