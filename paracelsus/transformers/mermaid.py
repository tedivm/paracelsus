from sqlalchemy.sql.schema import Column, MetaData, Table

from . import utils


class Mermaid:
    comment_format: str = "mermaid"
    metadata: MetaData

    def __init__(self, metaclass: MetaData) -> None:
        self.metadata = metaclass

    def _table(self, table: Table) -> str:
        output = f"  {table.name}"
        output += " {\n"
        columns = sorted(table.columns, key=utils.column_sort_key)
        for column in columns:
            output += self._column(column)
        output += "  }\n\n"
        return output

    def _column(self, column: Column) -> str:
        column_str = f"{column.type} {column.name}"

        if column.primary_key:
            if len(column.foreign_keys) > 0:
                column_str += " PK,FK"
            else:
                column_str += " PK"
        elif len(column.foreign_keys) > 0:
            column_str += " FK"

        options = []

        if column.nullable:
            options.append("nullable")

        if column.unique:
            options.append("unique")

        if column.index:
            options.append("indexed")

        if len(options) > 0:
            column_str += f' "{",".join(options)}"'

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
            left_table = key_parts[0]
            left_column = key_parts[1]
            left_operand = ""

            lcolumn = self.metadata.tables[left_table].columns[left_column]
            if lcolumn.unique or lcolumn.primary_key:
                left_operand = "||"
            else:
                left_operand = "}o"

            output += f"  {left_table} {left_operand}--{right_operand} {right_table} : {column_name}\n"
        return output

    def __str__(self) -> str:
        output = "erDiagram\n"
        for table in self.metadata.tables.values():
            output += self._table(table)

        for table in self.metadata.tables.values():
            for column in table.columns.values():
                if len(column.foreign_keys) > 0:
                    output += self._relationships(column)

        return output
