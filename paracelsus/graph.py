import importlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from sqlalchemy.schema import MetaData

from paracelsus.models.pattern import Pattern

from .config import Layouts
from .finders import ModuleFinder
from .transformers.dot import Dot
from .transformers.mermaid import Mermaid

transformers: Dict[str, type[Union[Mermaid, Dot]]] = {
    "mmd": Mermaid,
    "mermaid": Mermaid,
    "dot": Dot,
    "gv": Dot,
}

logger = logging.getLogger(__name__)


def to_module_name(root: Path, path: Path) -> str:
    """
    Converts a filesystem path to a Python dotted module string.
    Example: /root/app/models.py -> app.models
    """
    try:
        relative_path = path.resolve().relative_to(root)
    except ValueError:
        # Fallback if path is not relative to root (should not happen in normal usage)
        return path.name

    if path.is_file():
        clean_path = relative_path.with_suffix("")
    else:
        clean_path = relative_path

    return ".".join(clean_path.parts)


def _find_base_classes_by_pattern(
    base_class_path: str,
    python_dir: List[Path],
    current_root: Path,
) -> List[tuple[str, MetaData]]:
    """
    Finds all base classes matching a glob pattern and returns their MetaData.
    """
    if "*" not in base_class_path and "?" not in base_class_path:
        # No wildcards, return single base class
        module_path, class_name = base_class_path.split(":", 2)
        try:
            base_module = importlib.import_module(module_path)
            base_class = getattr(base_module, class_name)
            return [(module_path, base_class.metadata)]
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not import base class from {base_class_path}: {e}")

    # Extract pattern parts
    parts = base_class_path.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid base_class_path format: {base_class_path}")

    pattern_str, class_name = parts

    # Create pattern for finding base.py modules
    pattern = Pattern(mask=pattern_str)

    if any(pattern.errors):
        raise ValueError(pattern.serialized_errors)

    # Find all matching base.py files
    finder = ModuleFinder(current_root, pattern.tokens)
    base_metadata_list = []

    for file_path in finder.find():
        # Only consider base.py files
        if file_path.name != "base.py" and not file_path.name.endswith("base.py"):
            continue

        module_path = to_module_name(current_root, file_path)

        try:
            base_module = importlib.import_module(module_path)
            if hasattr(base_module, class_name):
                base_class = getattr(base_module, class_name)
                base_metadata_list.append((module_path, base_class.metadata))
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not import base class from {module_path}: {e}")
            continue

    if not base_metadata_list:
        raise ValueError(f"No base classes found matching pattern: {base_class_path}")

    return base_metadata_list


def _merge_metadata(metadata_list: List[tuple[str, MetaData]]) -> MetaData:
    """
    Merges multiple MetaData objects into a single MetaData.
    If there are table name conflicts, prefixes are added based on the module path.
    """
    merged_metadata = MetaData()

    for module_path, metadata in metadata_list:
        # Extract a prefix from module path to avoid conflicts
        # e.g., "project1.example.base" -> "project1_"
        parts = module_path.split(".")
        prefix = ""
        if len(parts) > 1:
            # Use first part as prefix (e.g., "project1")
            prefix = f"{parts[0]}_"

        for tablename, table in metadata.tables.items():
            # Check for conflicts
            prefixed_name = f"{prefix}{tablename}" if prefix else tablename

            # If there's a conflict and we have a prefix, use prefixed name
            if prefixed_name in merged_metadata.tables and prefix:
                logger.warning(
                    f"Table name conflict: '{tablename}' from {module_path} conflicts. "
                    f"Using prefixed name: '{prefixed_name}'"
                )
                final_name = prefixed_name
            elif tablename in merged_metadata.tables:
                # Conflict without prefix - use original name (tables are the same)
                final_name = tablename
            else:
                # No conflict
                final_name = tablename if not prefix else prefixed_name

            # Copy table to merged metadata
            if final_name not in merged_metadata.tables:
                if hasattr(table, "to_metadata"):
                    table.to_metadata(merged_metadata, name=final_name)
                else:
                    table.tometadata(merged_metadata, name=final_name)

    return merged_metadata


def get_graph_metadata(
    *,
    base_class_path: str,
    import_module: List[str],
    include_tables: Set[str],
    exclude_tables: Set[str],
    python_dir: List[Path],
    merge_namespace_metadata: bool = False,
) -> MetaData:
    """
    Builds a graph structure by importing modules and returns the filtered MetaData.
    This function separates the graph building logic from serialization, allowing
    tests to compare MetaData objects directly without parsing strings.
    """
    # Update the PYTHON_PATH to allow more module imports.
    sys.path.append(str(os.getcwd()))
    for dir in python_dir:
        sys.path.append(str(dir))

    current_root = Path.cwd()

    # Handle base class path with or without wildcards
    has_wildcards = "*" in base_class_path or "?" in base_class_path
    base_metadata_list = None

    if has_wildcards or (merge_namespace_metadata and has_wildcards):
        # Find all matching base classes and merge their metadata
        base_metadata_list = _find_base_classes_by_pattern(base_class_path, python_dir, current_root)

        if len(base_metadata_list) > 1:
            metadata = _merge_metadata(base_metadata_list)
        elif len(base_metadata_list) == 1:
            # Single base class found
            metadata = base_metadata_list[0][1]
        else:
            raise ValueError(f"No base classes found matching pattern: {base_class_path}")
    else:
        # No wildcards, use single base class
        module_path, class_name = base_class_path.split(":", 2)
        base_module = importlib.import_module(module_path)
        base_class = getattr(base_module, class_name)
        metadata = base_class.metadata

    # The modules holding the model classes have to be imported to get put in the metaclass model registry.
    # These modules aren't actually used in any way, so they are discarded.
    # They are also imported in scope of this function to prevent namespace pollution.
    for module_lookup_mask in import_module:
        module_path, import_modifier = module_lookup_mask, None

        if module_path.endswith(":*"):
            module_path, import_modifier = module_path.split(":", 1)

        pattern = Pattern(mask=module_path)

        if any(pattern.errors):
            raise ValueError(pattern.serialized_errors)

        finder = ModuleFinder(current_root, pattern.tokens)
        needs_wildcards_import = import_modifier == "*"

        for file_path in finder.find():
            module_path = to_module_name(current_root, file_path)

            # Check if already loaded to save time
            if module_path in sys.modules:
                continue

            try:
                if needs_wildcards_import:
                    exec(f"from {module_path} import *")
                else:
                    importlib.import_module(module_path)
            except ImportError as e:
                logger.error(f"Failed to load {module_path}: {e}")
                raise e

    # If we merged metadata from multiple base classes, we need to re-merge after models are imported
    # because models register themselves in the original base class metadata, not the merged one
    if base_metadata_list and len(base_metadata_list) > 1:
        # Re-collect metadata from all base classes after models have been imported
        updated_metadata_list = []
        for module_path, _ in base_metadata_list:
            try:
                base_module = importlib.import_module(module_path)
                # Extract class name from base_class_path
                _, class_name = base_class_path.split(":", 2)
                if hasattr(base_module, class_name):
                    base_class = getattr(base_module, class_name)
                    updated_metadata_list.append((module_path, base_class.metadata))
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not re-import base class from {module_path}: {e}")
                continue

        if updated_metadata_list:
            metadata = _merge_metadata(updated_metadata_list)

    # Keep only the tables which were included / not-excluded
    include_tables = resolve_included_tables(
        include_tables=include_tables, exclude_tables=exclude_tables, all_tables=set(metadata.tables.keys())
    )
    filtered_metadata = filter_metadata(metadata=metadata, include_tables=include_tables)

    return filtered_metadata


def serialize_metadata(
    metadata: MetaData,
    *,
    format: str,
    column_sort: str,
    omit_comments: bool = False,
    max_enum_members: int = 0,
    layout: Optional[Layouts] = None,
    type_parameter_delimiter: str = "-",
) -> str:
    """
    Serializes MetaData to a string representation in the specified format.
    """
    if format not in transformers:
        raise ValueError(f"Unknown Format: {format}")
    # Mermaid supports extra options (enum truncation + type parameter delimiter sanitization).
    if format in ["mermaid", "mmd"]:
        return str(
            Mermaid(
                metadata,
                column_sort,
                omit_comments=omit_comments,
                max_enum_members=max_enum_members,
                layout=layout,
                type_parameter_delimiter=type_parameter_delimiter,
            )
        )

    return str(Dot(metadata, column_sort, omit_comments=omit_comments, layout=layout))


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
    max_enum_members: int = 0,
    layout: Optional[Layouts] = None,
    type_parameter_delimiter: str = "-",
) -> str:
    """
    Builds a graph structure and returns it as a serialized string.

    This is a convenience wrapper that combines get_graph_metadata() and serialize_metadata()
    for backward compatibility.
    """
    metadata = get_graph_metadata(
        base_class_path=base_class_path,
        import_module=import_module,
        include_tables=include_tables,
        exclude_tables=exclude_tables,
        python_dir=python_dir,
    )

    return serialize_metadata(
        metadata,
        format=format,
        column_sort=column_sort,
        omit_comments=omit_comments,
        max_enum_members=max_enum_members,
        layout=layout,
        type_parameter_delimiter=type_parameter_delimiter,
    )


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
                    f"Some tables to include ({non_existent_tables}) don't exist "
                    f"within the found tables ({all_tables})."
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


def compare_metadata(actual: MetaData, expected: MetaData, omit_comments: bool = False) -> None:
    """
    Compares two MetaData objects and raises AssertionError if they differ.
    This function performs a structural comparison of two graph representations,
    checking tables, columns, types, constraints, and relationships.
    """

    actual_tables = set(actual.tables.keys())
    expected_tables = set(expected.tables.keys())

    # Check table names
    if actual_tables != expected_tables:
        missing = expected_tables - actual_tables
        extra = actual_tables - expected_tables
        error_msg = "Table mismatch:\n"
        if missing:
            error_msg += f"  Missing tables: {missing}\n"
        if extra:
            error_msg += f"  Extra tables: {extra}\n"
        raise AssertionError(error_msg)

    # Check each table's structure
    for table_name in expected_tables:
        actual_table = actual.tables[table_name]
        expected_table = expected.tables[table_name]

        actual_columns = {col.name: col for col in actual_table.columns}
        expected_columns = {col.name: col for col in expected_table.columns}

        # Check column names
        if set(actual_columns.keys()) != set(expected_columns.keys()):
            missing = set(expected_columns.keys()) - set(actual_columns.keys())
            extra = set(actual_columns.keys()) - set(expected_columns.keys())
            error_msg = f"Column mismatch in table '{table_name}':\n"
            if missing:
                error_msg += f"  Missing columns: {missing}\n"
            if extra:
                error_msg += f"  Extra columns: {extra}\n"
            raise AssertionError(error_msg)

        # Check each column's properties
        for col_name in expected_columns.keys():
            actual_col = actual_columns[col_name]
            expected_col = expected_columns[col_name]

            # Check type
            actual_type_str = str(actual_col.type)
            expected_type_str = str(expected_col.type)
            if actual_type_str != expected_type_str:
                raise AssertionError(
                    f"Type mismatch in table '{table_name}', column '{col_name}': "
                    f"expected {expected_type_str}, got {actual_type_str}"
                )

            # Check constraints
            actual_pk = actual_col.primary_key
            expected_pk = expected_col.primary_key
            if actual_pk != expected_pk:
                raise AssertionError(
                    f"Primary key mismatch in table '{table_name}', column '{col_name}': "
                    f"expected {expected_pk}, got {actual_pk}"
                )

            actual_fk_count = len(actual_col.foreign_keys)
            expected_fk_count = len(expected_col.foreign_keys)
            if actual_fk_count != expected_fk_count:
                raise AssertionError(
                    f"Foreign key count mismatch in table '{table_name}', column '{col_name}': "
                    f"expected {expected_fk_count}, got {actual_fk_count}"
                )

            # Check nullable
            if actual_col.nullable != expected_col.nullable:
                raise AssertionError(
                    f"Nullable mismatch in table '{table_name}', column '{col_name}': "
                    f"expected {expected_col.nullable}, got {actual_col.nullable}"
                )

            # Check comments (if not omitted)
            if not omit_comments:
                actual_comment = actual_col.comment
                expected_comment = expected_col.comment
                if actual_comment != expected_comment:
                    raise AssertionError(
                        f"Comment mismatch in table '{table_name}', column '{col_name}': "
                        f"expected {expected_comment!r}, got {actual_comment!r}"
                    )

        # Check foreign key relationships
        actual_fks: set[tuple[str, ...]] = set()
        for col in actual_table.columns:
            for fk in col.foreign_keys:
                # Format: (table_name, column_name) -> (target_table, target_column)
                target_parts = fk.target_fullname.split(".")
                target_table = ".".join(target_parts[:-1])
                target_column = target_parts[-1]
                actual_fks.add((table_name, col.name, target_table, target_column))

        expected_fks: set[tuple[str, ...]] = set()
        for col in expected_table.columns:
            for fk in col.foreign_keys:
                target_parts = fk.target_fullname.split(".")
                target_table = ".".join(target_parts[:-1])
                target_column = target_parts[-1]
                expected_fks.add((table_name, col.name, target_table, target_column))

        if actual_fks != expected_fks:
            missing_fks: set[tuple[str, ...]] = expected_fks - actual_fks
            extra_fks: set[tuple[str, ...]] = actual_fks - expected_fks
            error_msg = f"Foreign key mismatch in table '{table_name}':\n"
            if missing:
                error_msg += f"  Missing FKs: {missing_fks}\n"
            if extra:
                error_msg += f"  Extra FKs: {extra_fks}\n"
            raise AssertionError(error_msg)
