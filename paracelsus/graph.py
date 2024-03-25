import importlib
import os
import sys
from pathlib import Path
from typing import List

from .transformers.dot import Dot
from .transformers.mermaid import Mermaid

transformers = {
    "mmd": Mermaid,
    "mermaid": Mermaid,
    "dot": Dot,
    "gv": Dot,
}


def get_graph_string(
    base_class_path: str,
    import_module: List[str],
    python_dir: List[Path],
    format: str,
) -> str:
    # Update the PYTHON_PATH to allow more module imports.
    sys.path.append(str(os.getcwd()))
    for dir in python_dir:
        sys.path.append(str(dir))

    # Import the base class so the metadata class can be extracted from it.
    # The metadata class is passed to the transformer.
    module_path, class_name = base_class_path.split(":", 2)
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

    # Grab a transformer.
    if format not in transformers:
        raise ValueError(f"Unknown Format: {format}")
    transformer = transformers[format]

    # Save the graph structure to string.
    return str(transformer(metadata))
