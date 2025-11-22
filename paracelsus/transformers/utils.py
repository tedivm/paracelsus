from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql import ColumnCollection


def key_based_column_sort(column: Column) -> str:
    if column.primary_key:
        prefix = "01"
    elif len(column.foreign_keys):
        prefix = "02"
    else:
        prefix = "03"
    return f"{prefix}_{column.name}"


def sort_columns(table_columns: ColumnCollection, column_sort: str) -> list:
    match column_sort:
        case "preserve-order":
            columns = [column for column in table_columns]
        case _:
            columns = sorted(table_columns, key=key_based_column_sort)

    return columns


def is_unique(column: Column) -> bool:
    """Determine if a column is unique.

    A single column is considered unique in any of the following cases:

    - It has the ``unique`` attribute set to ``True``.
    - It is a primary key.
    - There is a ``UniqueConstraint`` defined on the table that includes **only** this column.
    """
    if column.unique or column.primary_key:
        return True

    # It's unique if there's a UniqueConstraint on just this column.
    for constraint in column.table.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.columns.keys() == [column.key]:
            return True

    return False
