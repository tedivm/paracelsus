import logging
import textwrap
from typing import Optional

import sqlalchemy
from sqlalchemy.sql.schema import Column, MetaData, Table

from .utils import sort_columns

logger = logging.getLogger(__name__)


class Mermaid:
    comment_format: str = "mermaid"
    metadata: MetaData
    column_sort: str
    omit_comments: bool
    max_enum_members: int
    layout: Optional[str]

    def __init__(
        self,
        metaclass: MetaData,
        column_sort: str,
        omit_comments: bool = False,
        max_enum_members: int = 0,
        layout: Optional[str] = None,
    ) -> None:
        self.metadata = metaclass
        self.column_sort = column_sort
        self.omit_comments = omit_comments
        self.max_enum_members = max_enum_members
        self.layout: Optional[str] = layout

    def _table(self, table: Table) -> str:
        output = f"  {table.name}"
        output += " {\n"
        columns = sort_columns(table_columns=table.columns, column_sort=self.column_sort)
        for column in columns:
            output += self._column(column)
        output += "  }\n\n"
        return output

    def _column(self, column: Column) -> str:
        options = []
        col_type = column.type
        is_enum = isinstance(col_type, sqlalchemy.Enum)
        column_str = f"ENUM {column.name}" if is_enum else f"{col_type} {column.name}"

        if column.primary_key:
            if len(column.foreign_keys) > 0:
                column_str += " PK,FK"
            else:
                column_str += " PK"
        elif len(column.foreign_keys) > 0:
            column_str += " FK"
        elif column.unique:
            column_str += " UK"

        if column.comment and not self.omit_comments:
            options.append(column.comment)

        if column.nullable:
            options.append("nullable")

        if column.index:
            options.append("indexed")

        # For ENUM, add values as a separate part
        option_str = ",".join(options)

        if is_enum and self.max_enum_members > 0:
            enum_list = list(col_type.enums)  # type: ignore # MyPy will fail here, but this code works.
            if len(enum_list) <= self.max_enum_members:
                enum_values = ", ".join(enum_list)
            else:
                displayed_values = enum_list[: self.max_enum_members - 1]
                enum_values = ", ".join(displayed_values) + ", ..., " + enum_list[-1]

            if option_str:
                option_str += f"; values: {enum_values}"
            else:
                option_str = f"values: {enum_values}"

        if option_str:
            column_str += f' "{option_str}"'

        return f"    {column_str}\n"

    def _relationships(self, column: Column) -> str:
        output = ""

        column_name = column.name
        right_table = column.table.name

        if column.unique:
            right_operand = "o|"
        else:
            right_operand = "o{"

        for foreign_key in column.foreign_keys:
            key_parts = foreign_key.target_fullname.split(".")
            left_table = ".".join(key_parts[:-1])
            left_column = key_parts[-1]
            left_operand = ""

            # We don't add the connection to the fk table if the latter
            # is not included in our graph.
            if left_table not in self.metadata.tables:
                logger.warning(
                    f"Table '{right_table}.{column_name}' is a foreign key to '{left_table}' "
                    "which is not included in the graph, skipping the connection."
                )
                continue

            lcolumn = self.metadata.tables[left_table].columns[left_column]
            if lcolumn.unique or lcolumn.primary_key:
                left_operand = "||"
            else:
                left_operand = "}o"

            output += f"  {left_table.split('.')[-1]} {left_operand}--{right_operand} {right_table} : {column_name}\n"
        return output

    def __str__(self) -> str:
        output = ""
        if self.layout:
            yaml_front_matter = textwrap.dedent(f"""
            ---
                config:
                    layout: {self.layout}
            ---
            """)
            output = yaml_front_matter + output
        output += "erDiagram\n"
        for table in self.metadata.tables.values():
            output += self._table(table)

        for table in self.metadata.tables.values():
            for column in table.columns.values():
                if len(column.foreign_keys) > 0:
                    output += self._relationships(column)

        return output
