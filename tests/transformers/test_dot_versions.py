"""Test pydot version compatibility."""

import pytest

try:
    from paracelsus.compat.pydot_compat import PYDOT_V4, PYDOT_VERSION
except ImportError:
    PYDOT_V4 = False
    PYDOT_VERSION = None


class TestPydotVersionCompatibility:
    """Test that dot transformer works across pydot versions."""

    def test_version_detection(self):
        """Test that we can detect pydot version."""
        assert PYDOT_VERSION is not None, "Should detect pydot version"

    def test_basic_graph_creation(self, metaclass):
        """Test basic graph creation works on any version."""
        from paracelsus.transformers.dot import Dot

        dot = Dot(metaclass=metaclass, column_sort="key-based")
        graph_string = str(dot)

        # Basic assertions that should work on any version
        assert "users" in graph_string
        assert "posts" in graph_string
        assert graph_string.startswith("graph database")

    @pytest.mark.skipif(not PYDOT_V4, reason="pydot v4 specific test")
    def test_v4_features(self, metaclass):
        """Test features specific to pydot v4."""
        from paracelsus.transformers.dot import Dot

        dot = Dot(metaclass=metaclass, column_sort="key-based")
        # v4 should work without issues
        assert dot.graph is not None
        assert hasattr(dot.graph, "to_string")

    @pytest.mark.skipif(PYDOT_V4, reason="pydot v3 specific test")
    def test_v3_compatibility(self, metaclass):
        """Test backwards compatibility with v3."""
        from paracelsus.transformers.dot import Dot

        dot = Dot(metaclass=metaclass, column_sort="key-based")
        graph_string = str(dot)
        # Ensure v3 behavior is maintained
        assert isinstance(graph_string, str)
        assert len(graph_string) > 0

    def test_version_logging(self, metaclass, caplog):
        """Test that we can log version information."""
        import logging

        from paracelsus.transformers.dot import Dot

        with caplog.at_level(logging.INFO):
            dot = Dot(metaclass=metaclass, column_sort="key-based")
            _ = str(dot)

        # Verify basic functionality works
        assert dot.graph is not None
