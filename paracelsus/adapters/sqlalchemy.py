from sqlalchemy.sql import schema

from .base import Column, ForeignKey, ModelAdapter, Table


class SQLAlchemyModelAdapter(ModelAdapter):
    def __init__(self, metadata: schema.MetaData):
        self.metadata = metadata

    def tables(self) -> dict[str, Table]:
        return {name: adapt_table(table) for name, table in self.metadata.tables.items()}


def adapt_table(model_table: schema.Table) -> Table:
    return SQLAlchemyTable(model_table)


def adapt_column(c: schema.Column, table: Table) -> Column:
    return Column(
        table=table,
        name=c.name,
        type=str(c.type),
        primary_key=c.primary_key,
        nullable=c.nullable,
        foreign_keys={adapt_foreign_key(fk) for fk in c.foreign_keys},
        unique=c.unique,
        index=c.index,
    )


def adapt_foreign_key(fk: schema.ForeignKey) -> ForeignKey:
    return ForeignKey(target_fullname=fk.target_fullname)


class SQLAlchemyTable(Table):
    def __init__(self, table: schema.Table) -> None:
        super().__init__(name=table.name, columns={name: adapt_column(c, self) for name, c in table.columns.items()})
