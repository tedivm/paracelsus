from pathlib import Path

from paracelsus.pyproject import get_pyproject_settings


def test_pyproject(package_path: Path):
    settings = get_pyproject_settings(package_path / "pyproject.toml")
    assert settings.base == "example.base:Base"
    assert settings.imports == ["example.models"]
