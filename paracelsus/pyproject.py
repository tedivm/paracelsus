from pathlib import Path
from .config import ParacelsusTomlConfig

try:
    import tomllib
except ImportError:
    import toml as tomllib  # type: ignore


def get_pyproject_settings(config_file: Path) -> ParacelsusTomlConfig:
    if not config_file.exists():
        return ParacelsusTomlConfig()

    data = tomllib.loads(config_file.read_bytes().decode())

    return ParacelsusTomlConfig(**data.get("tool", {}).get("paracelsus", {}))
