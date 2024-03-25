import os
import tomllib
from pathlib import Path
from typing import Any, Dict


def get_pyproject_settings(dir: Path = Path(os.getcwd())) -> Dict[str, Any] | None:
    pyproject = dir / "pyproject.toml"

    if not pyproject.exists():
        return None

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    return data.get("tool", {}).get("paracelsus", None)
