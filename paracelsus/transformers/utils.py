from typing import List

from sqlalchemy.sql.schema import Column, MetaData, Table


def column_key_function(column: Column):
    if column.primary_key:
        prefix = "01"
    elif len(column.foreign_keys):
        prefix = "02"
    else:
        prefix = "03"
    return f"{prefix}_{column.name}"
