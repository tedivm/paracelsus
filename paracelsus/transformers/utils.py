from sqlalchemy.sql.schema import Column
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
