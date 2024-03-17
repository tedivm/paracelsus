import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Set


class ModelAdapter(ABC):
    @abstractmethod
    def tables(self) -> dict[str, "Table"]:
        ...

    def column_sort_key(self, column: "Column") -> str:
        if column.primary_key:
            prefix = "01"
        elif len(column.foreign_keys):
            prefix = "02"
        else:
            prefix = "03"
        return f"{prefix}_{column.name}"


@dataclass(eq=True, frozen=True)
class Table:
    name: str
    columns: dict[str, "Column"]


@dataclass(eq=True, frozen=True)
class Column:
    table: Table
    name: str
    type: str
    primary_key: bool
    nullable: bool | None
    foreign_keys: Set["ForeignKey"]
    unique: bool | None
    index: bool | None


@dataclass(eq=True, frozen=True)
class ForeignKey:
    target_fullname: str


def get_adapter_for_base_class(base_class_path: str, import_module: list[str]) -> ModelAdapter:
    """Find the right adapter for the base class; two are supported: SQLAlchemy and Django.

    First, if the base class is _just_ a dot-separated string, we treat it as the Django settings
    object, bootstrap django, and load it.

    If the base class is ":"-separated, and the class has a `metadata` attribute, then we
    treat it as a SQLAlchemy object.

    If neither of those things are true, we bail.
    """

    # Import the base class so the metadata class can be extracted from it.
    # The metadata class is passed to the transformer.
    try:
        module_path, class_name = base_class_path.split(":", 2)
    except ValueError:
        # django path. NOTE: does not work.
        return get_django_adapter(settings_module=base_class_path)

    return get_sqlalchemy_adapter(module_path, class_name, import_module)


def get_django_adapter(settings_module: str) -> ModelAdapter:
    from .django import DjangoModelAdapter

    return DjangoModelAdapter.from_settings(settings_module)


def get_sqlalchemy_adapter(module_path, class_name, import_module):
    # Import the base class so the metadata class can be extracted from it.
    # The metadata class is passed to the transformer.
    base_module = importlib.import_module(module_path)
    base_class = getattr(base_module, class_name)
    metadata = base_class.metadata

    # The modules holding the model classes have to be imported to get put in the metaclass model registry.
    # These modules aren't actually used in any way, so they are discarded.
    # They are also imported in scope of this function to prevent namespace pollution.
    for module in import_module:
        if ":*" in module:
            # Sure, execs are gross, but this is the only way to dynamically import wildcards.
            exec(f"from {module[:-2]} import *")
        else:
            importlib.import_module(module)

    from .sqlalchemy import SQLAlchemyModelAdapter

    return SQLAlchemyModelAdapter(metadata=metadata)
