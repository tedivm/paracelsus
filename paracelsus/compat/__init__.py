"""Compatibility layer for pydot v3 and v4."""

from paracelsus.compat.pydot_compat import (
    PYDOT_V4,
    PYDOT_VERSION,
    Dot,
    Edge,
    Node,
)

__all__ = ["Dot", "Node", "Edge", "PYDOT_V4", "PYDOT_VERSION"]
