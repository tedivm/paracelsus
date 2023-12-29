import pydot  # type: ignore
from sqlalchemy.sql.schema import MetaData, Table

from . import utils


class Dot:
    comment_format: str = "dot"
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
            for column in table.columns:
                for foreign_key in column.foreign_keys:
                    key_parts = foreign_key.target_fullname.split(".")
                    left_table = key_parts[0]
                    left_column = key_parts[1]
                    edge = pydot.Edge(left_table, table.name)
                    edge.set_label(column.name)
                    edge.set_dir("both")

                    edge.set_arrowhead("none")
                    if not column.unique:
                        edge.set_arrowhead("crow")

                    l_column = self.metadata.tables[left_table].columns[left_column]
                    edge.set_arrowtail("none")
                    if not l_column.unique and not l_column.primary_key:
                        edge.set_arrowtail("crow")

                    self.graph.add_edge(edge)

    def _table_label(self, table: Table) -> str:
        column_output = ""
        columns = sorted(table.columns, key=utils.column_sort_key)
        for column in columns:
            attributes = set([])
            if column.primary_key:
                attributes.add("Primary Key")

            if len(column.foreign_keys) > 0:
                attributes.add("Foreign Key")

            if column.unique:
                attributes.add("Unique")

            column_output += f'        <tr><td align="left">{column.type}</td><td align="left">{column.name}</td><td>{", ".join(sorted(attributes))}</td></tr>\n'

        return f"""<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
        <tr><td colspan="3" bgcolor="lightblue"><b>{table.name}</b></td></tr>
{column_output.rstrip()}
    </table>
>"""

    def __str__(self) -> str:
        return self.graph.to_string()
