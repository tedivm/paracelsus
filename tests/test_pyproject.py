from paracelsus.pyproject import get_pyproject_settings


def test_pyproject(package_path):
    settings = get_pyproject_settings(package_path)
    assert "base" in settings
    assert "imports" in settings
    assert settings["base"] == "example.base:Base"
    assert "example.models" in settings["imports"]


def test_pyproject_none():
    settings = get_pyproject_settings()
    assert settings == {}
