import os
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except:  # noqa: E722
    import toml as tomllib  # type: ignore


def get_pyproject_settings(dir: Path = Path(os.getcwd())) -> Dict[str, Any]:
    pyproject = dir / "pyproject.toml"

    if not pyproject.exists():
        return {}

    with open(pyproject, "rb") as f:
        data = tomllib.loads(f.read().decode())

    return data.get("tool", {}).get("paracelsus", {})
