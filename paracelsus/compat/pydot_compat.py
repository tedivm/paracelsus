"""Compatibility layer for pydot v3 and v4."""

from typing import Optional

try:
    import pydot
    from packaging import version

    PYDOT_VERSION: Optional[version.Version] = version.parse(pydot.__version__)
    PYDOT_V4 = PYDOT_VERSION is not None and PYDOT_VERSION.major >= 4
except Exception:
    PYDOT_V4 = False
    PYDOT_VERSION = None

# Export standard pydot classes
from pydot import Dot, Edge, Node  # noqa: F401

__all__ = ["Dot", "Node", "Edge", "PYDOT_V4", "PYDOT_VERSION"]
