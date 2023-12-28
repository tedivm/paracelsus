from typing import List

import pydot
from sqlalchemy.sql.schema import Column, MetaData, Table


class Dot:
    metadata: MetaData
    graph: pydot.Dot

    def __init__(self, metaclass: MetaData) -> None:
        self.metadata = metaclass
        self.graph = pydot.Dot("database", graph_type="graph")

        for table in self.metadata.tables.values():
            node = pydot.Node(name=table.name)
            node.set_label(self._table_label(table))
            node.set_shape("none")
            node.set_margin("0")
            self.graph.add_node(node)

            for column in table.columns.values():
                for foreign_key in column.foreign_keys:
                    key_parts = foreign_key.target_fullname.split(".")
                    left_table = key_parts[0]
                    left_column = key_parts[1]
                    edge = pydot.Edge(left_table, table.name)

                    if not column.unique:
                        edge.set_arrowhead("crow")
                    else:
                        edge.set_arrowhead("none")

                    l_column = self.metadata.tables[left_table].columns[left_column]
                    if not l_column.unique and not l_column.primary_key:
                        edge.set_arrowtail("crow")
                    else:
                        edge.set_arrowtail("none")

                    edge.set_label(column.name)

                    edge.set_dir("both")
                    # "edge [arrowhead=crow, arrowtail=none, dir=both]"

                    self.graph.add_edge(edge)

    def _table_label(self, table: Table) -> str:
        column_output = ""
        for column in table.columns.values():
            relationship = ""
            if column.primary_key:
                if len(column.foreign_keys) > 0:
                    relationship += " PK,FK"
                else:
                    relationship += " PK"
            elif len(column.foreign_keys) > 0:
                relationship += " FK"

            column_output += f'        <tr><td align="left">{column.type}</td><td align="left">{column.name}</td><td>{relationship}</td></tr>\n'

        return f"""<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
        <tr><td colspan="3" bgcolor="lightblue"><b>{table.name}</b></td></tr>
{column_output.rstrip()}
    </table>
>"""

    def __str__(self) -> str:
        return self.graph.to_string()
