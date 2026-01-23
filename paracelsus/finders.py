from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Set


@dataclass(frozen=True, eq=True)
class GlobNode:
    pattern: str
    next: Optional["GlobNode"] = None

    @staticmethod
    def nodify(tokens: list[str]) -> Optional["GlobNode"]:
        head = None
        for part in reversed(tokens):
            new_node = GlobNode(pattern=part, next=head)
            head = new_node
        return head

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, GlobNode) and self is value

    @property
    def is_final(self):
        return self.next is None

    def __repr__(self):
        return f"Node({self.pattern})"


@dataclass(frozen=True)
class SearchState:
    """Represents a snapshot of the traversal cursor."""

    path: Path
    node: GlobNode


class ModuleFinder:
    def __init__(self, root: Path, segments: list[str]):
        self.root = root
        self.head = GlobNode.nodify(segments)

        self.queue: deque[SearchState] = deque()
        # To prevent infinite loops with symlinks or redundant '**' paths
        self.visited: Set[SearchState] = set()

    def find(self) -> Generator[Path, None, None]:
        """
        Finds all modules that match the glob-like pattern for Python modules.

        Supports patterns like:
            - example.*.models
            - example.fo?.models
            - example.*.*.models
            - example.**.api.*.models
            - example.api.v[12].models
            - example.api.v[0-9].models
            - example.api.v[!1].models

        """
        if self.head is None:
            return

        # Initialize state
        self.queue.append(SearchState(self.root, self.head))

        while self.queue:
            state = self.queue.popleft()

            # Optimization: distinct paths to the same state are redundant
            if state in self.visited:
                continue
            self.visited.add(state)

            yield from self._process_state(state)

    def _process_state(self, state: SearchState) -> Generator[Path, None, None]:
        """
        Implement BFS to search for files and directories matching the given pattern.
        """
        node = state.node
        path = state.path

        # === 1. Recursive Wildcard (**) ===
        if node.pattern == "**":
            # Branch A: Skip (0 matches).
            # Move to next node, keep path same.
            if node.next:
                self.queue.append(SearchState(path, node.next))

            # Branch B: Consume (1+ matches).
            # Stay on current node, move deeper into filesystem.
            for child in self._safe_iterdir(path):
                if child.is_dir():
                    self.queue.append(SearchState(child, node))

        else:
            for child in self._safe_iterdir(path):
                is_match = False

                if child.is_dir():
                    if child.match(node.pattern):
                        is_match = True

                elif child.is_file():
                    if Path(child.stem).match(node.pattern):
                        is_match = True

                if not is_match:
                    continue

                if node.is_final and self._is_valid_module(child):
                    yield child

                elif node.next is not None and child.is_dir():
                    self.queue.append(SearchState(child, node.next))

    def _safe_iterdir(self, path: Path) -> Generator[Path, None, None]:
        """Safe wrapper around iterdir to handle permission errors."""
        try:
            if path.is_dir():
                yield from path.iterdir()
        except PermissionError:
            pass

    def _is_valid_module(self, path: Path) -> bool:
        """
        Determines if a path is a valid python module.
        1. File: my_module.py (but not __init__.py)
        2. Package: my_package/ (must contain __init__.py)
        3. Supports PEP 420 Namespace Packages.
        """

        name = path.name

        # 1. Ignore common garbage/internal directories
        if name == "__pycache__" or name.startswith("."):
            return False

        if path.is_file():
            return path.suffix == ".py" and path.name != "__init__.py"

        if path.is_dir():
            return (path / "__init__.py").exists() or name.isidentifier()

        return False
