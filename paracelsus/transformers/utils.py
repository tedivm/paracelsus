from sqlalchemy.sql.schema import Column


def column_sort_key(column: Column):
    if column.primary_key:
        prefix = "01"
    elif len(column.foreign_keys):
        prefix = "02"
    else:
        prefix = "03"
    return f"{prefix}_{column.name}"
