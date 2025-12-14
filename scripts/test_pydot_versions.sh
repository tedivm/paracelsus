#!/bin/bash
# Test paracelsus against multiple pydot versions locally
# Usage: ./scripts/test_pydot_versions.sh [version1] [version2] [...]
#
# Examples:
#   ./scripts/test_pydot_versions.sh              # Test latest v3 and v4
#   ./scripts/test_pydot_versions.sh 3.0.2 4.0.1  # Test specific versions
#   ./scripts/test_pydot_versions.sh 3.0.4        # Test only specified version

set -e

# Get the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if virtual environment exists, create if not
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Virtual environment not found. Running 'make install'..."
    cd "$PROJECT_ROOT"
    make install
    echo ""
fi

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

echo "=== Pydot Version Compatibility Test ==="
echo ""

# Function to get latest version for a major version
get_latest_version() {
    local major_version=$1
    pip index versions pydot 2>/dev/null | grep "Available versions:" | sed 's/Available versions: //' | tr ',' '\n' | sed 's/^[ \t]*//' | grep "^${major_version}\." | head -n1
}

# Default to latest versions if no arguments provided
if [ $# -eq 0 ]; then
    echo "Looking up latest pydot versions..."
    V3_LATEST=$(get_latest_version "3")
    V4_LATEST=$(get_latest_version "4")

    if [ -z "$V3_LATEST" ] || [ -z "$V4_LATEST" ]; then
        echo "⚠️  Failed to fetch latest versions from PyPI, using fallback defaults"
        VERSIONS=("3.0.4" "4.0.1")
    else
        VERSIONS=("$V3_LATEST" "$V4_LATEST")
    fi
    echo "Testing latest versions: ${VERSIONS[*]}"
else
    VERSIONS=("$@")
    echo "Testing specified versions: ${VERSIONS[*]}"
fi
echo ""

# Store original pydot version
ORIGINAL_VERSION=$(pip show pydot 2>/dev/null | grep Version | cut -d' ' -f2 || echo "none")

echo "Original pydot version: $ORIGINAL_VERSION"
echo ""

# Track results
PASSED=0
FAILED=0
FAILED_VERSIONS=""

for version in "${VERSIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing with pydot==$version"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Install specific version
    if pip install "pydot==$version" --quiet 2>/dev/null; then
        echo "✓ Installed pydot $version"

        # Verify installation
        INSTALLED=$(python -c "import pydot; print(pydot.__version__)")
        echo "  Verified: $INSTALLED"

        # Run tests
        if pytest tests/ -v --tb=short; then
            echo "✅ Tests PASSED with pydot $version"
            ((PASSED++))
        else
            echo "❌ Tests FAILED with pydot $version"
            ((FAILED++))
            FAILED_VERSIONS="$FAILED_VERSIONS $version"
        fi
    else
        echo "⚠️  Could not install pydot $version"
        echo "❌ Tests FAILED with pydot $version (installation failed)"
        ((FAILED++))
        FAILED_VERSIONS="$FAILED_VERSIONS $version"
    fi

    echo ""
done

# Restore original version if it was installed
if [ "$ORIGINAL_VERSION" != "none" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Restoring original pydot version: $ORIGINAL_VERSION"
    pip install "pydot==$ORIGINAL_VERSION" --quiet
    echo "✓ Restored"
fi

# Deactivate virtual environment
deactivate

echo ""
echo "=== Test Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo "Failed versions:$FAILED_VERSIONS"
    exit 1
else
    echo "🎉 All versions tested successfully!"
    exit 0
fi
