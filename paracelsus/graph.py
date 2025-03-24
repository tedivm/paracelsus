import importlib
import os
import sys
from pathlib import Path
import re
from typing import List, Set, Optional, Dict, Union

from sqlalchemy.schema import MetaData

from .transformers.dot import Dot
from .transformers.mermaid import Mermaid

transformers: Dict[str, type[Union[Mermaid, Dot]]] = {
    "mmd": Mermaid,
    "mermaid": Mermaid,
    "dot": Dot,
    "gv": Dot,
}


def get_graph_string(
    *,
    base_class_path: str,
    import_module: List[str],
    include_tables: Set[str],
    exclude_tables: Set[str],
    python_dir: List[Path],
    format: str,
    column_sort: str,
    omit_comments: bool = False,
    layout: Optional[str] = None,
) -> str:
    # Update the PYTHON_PATH to allow more module imports.
    sys.path.append(str(os.getcwd()))
    for dir in python_dir:
        sys.path.append(str(dir))

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
    if format not in transformers:
        raise ValueError(f"Unknown Format: {format}")
    transformer = transformers[format]

    # Keep only the tables which were included / not-excluded
    include_tables = resolve_included_tables(
        include_tables=include_tables, exclude_tables=exclude_tables, all_tables=set(metadata.tables.keys())
    )
    filtered_metadata = filter_metadata(metadata=metadata, include_tables=include_tables)

    # Save the graph structure to string.
    return str(transformer(filtered_metadata, column_sort, omit_comments=omit_comments, layout=layout))


def resolve_included_tables(
    include_tables: Set[str],
    exclude_tables: Set[str],
    all_tables: Set[str],
) -> Set[str]:
    """Resolves the final set of tables to include in the graph.

    Given sets of inclusions and exclusions and the set of all tables we define
    the following cases are:
    - Empty inclusion and empty exclusion -> include all tables.
    - Empty inclusion and some exclusions -> include all tables except the ones in the exclusion set.
    - Some inclusions and empty exclusion -> make sure tables in the inclusion set are present in
        all tables then include the tables in the inclusion set.
    - Some inclusions and some exclusions -> not resolvable, an error is raised.
    """
    match len(include_tables), len(exclude_tables):
        case 0, 0:
            return all_tables
        case 0, int():
            excluded = {table for table in all_tables if any(re.match(pattern, table) for pattern in exclude_tables)}
            return all_tables - excluded
        case int(), 0:
            included = {table for table in all_tables if any(re.match(pattern, table) for pattern in include_tables)}

            if not included:
                non_existent_tables = include_tables - all_tables
                raise ValueError(
                    f"Some tables to include ({non_existent_tables}) don't exist"
                    "withinthe found tables ({all_tables})."
                )
            return included
        case _:
            raise ValueError(
                f"Only one or none of include_tables ({include_tables}) or exclude_tables"
                f"({exclude_tables}) can contain values."
            )


def filter_metadata(
    metadata: MetaData,
    include_tables: Set[str],
) -> MetaData:
    """Create a subset of the metadata based on the tables to include."""
    filtered_metadata = MetaData()
    for tablename, table in metadata.tables.items():
        if tablename in include_tables:
            if hasattr(table, "to_metadata"):
                # to_metadata is the new way to do this, but it's only available in newer versions of SQLAlchemy.
                table = table.to_metadata(filtered_metadata)
            else:
                # tometadata is deprecated, but we still need to support it for older versions of SQLAlchemy.
                table = table.tometadata(filtered_metadata)

    return filtered_metadata
