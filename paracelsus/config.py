from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Final


class Formats(str, Enum):
    mermaid = "mermaid"
    mmd = "mmd"
    dot = "dot"
    gv = "gv"


class ColumnSorts(str, Enum):
    key_based = "key-based"
    preserve = "preserve-order"


class Layouts(str, Enum):
    dagre = "dagre"
    elk = "elk"


SORT_DEFAULT: Final[ColumnSorts] = ColumnSorts.key_based
OMIT_COMMENTS_DEFAULT: Final[bool] = False
MAX_ENUM_MEMBERS_DEFAULT: Final[int] = 3
TYPE_PARAMETER_DELIMITER_DEFAULT: Final[str] = "-"


def validate_layout(*, format: Formats, layout: Layouts | None) -> None:
    """Validate that the layout parameter is only used with the mermaid format."""
    if layout and format != Formats.mermaid:
        raise ValueError("The `layout` parameter can only be used with the `mermaid` format.")


@dataclass(frozen=True)
class ParacelsusTomlConfig:
    """Structure containing configuration options loaded from ``pyproject.toml``.

    They all have default values, so that missing options can be handled gracefully.
    """

    base: str = ""
    imports: list[str] = field(default_factory=list)
    include_tables: list[str] = field(default_factory=list)
    exclude_tables: list[str] = field(default_factory=list)
    column_sort: ColumnSorts = SORT_DEFAULT
    omit_comments: bool = OMIT_COMMENTS_DEFAULT
    max_enum_members: int = MAX_ENUM_MEMBERS_DEFAULT
    type_parameter_delimiter: str = TYPE_PARAMETER_DELIMITER_DEFAULT


@dataclass(frozen=True)
class ParacelsusSettingsForGraph:
    """Structure containing all computed settings for invoking the graph generation.

    They are all mandatory. If need be, default values should be provided either at the
    CLI argument parsing level, or when loading from the ``pyproject.toml`` configuration.
    """

    base_class_path: str
    import_module: list[str]
    include_tables: set[str]
    exclude_tables: set[str]
    python_dir: list[Path]
    format: Formats
    column_sort: ColumnSorts
    omit_comments: bool
    max_enum_members: int
    layout: Layouts | None
    type_parameter_delimiter: str

    def __post_init__(self) -> None:
        validate_layout(format=self.format, layout=self.layout)


@dataclass(frozen=True)
class ParacelsusSettingsForInject:
    """Structure containing all computed settings for invoking the graph injection.

    They are all mandatory. If need be, default values should be provided either at the
    CLI argument parsing level, or when loading from the ``pyproject.toml`` configuration.
    """

    graph_settings: ParacelsusSettingsForGraph
    file: Path
    replace_begin_tag: str
    replace_end_tag: str
    check: bool
