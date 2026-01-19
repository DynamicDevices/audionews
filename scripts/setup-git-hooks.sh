#!/bin/bash
#
# Setup script to install git pre-commit hook
# Run this after cloning the repository
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Copy pre-commit hook
cat > "$PRE_COMMIT_HOOK" << 'HOOK_EOF'
#!/bin/bash
#
# Git pre-commit hook for linting
# Checks Python syntax, JSON validity, and basic code quality
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Running pre-commit linting checks..."

# Track if any errors were found
ERRORS=0

# Function to check Python syntax
check_python_syntax() {
    local file="$1"
    if [[ "$file" == *.py ]]; then
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${RED}❌ Python syntax error in: $file${NC}"
            python3 -m py_compile "$file" 2>&1 || true
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    fi
    return 0
}

# Function to check JSON validity
check_json_syntax() {
    local file="$1"
    if [[ "$file" == *.json ]]; then
        if ! python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
            echo -e "${RED}❌ JSON syntax error in: $file${NC}"
            python3 -c "import json; json.load(open('$file'))" 2>&1 || true
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    fi
    return 0
}

# Function to check for common Python issues
check_python_issues() {
    local file="$1"
    if [[ "$file" == *.py ]]; then
        # Check for trailing whitespace (warn only)
        if grep -q "[[:space:]]$" "$file"; then
            echo -e "${YELLOW}⚠️  Trailing whitespace found in: $file${NC}"
        fi
        
        # Check for tabs (should use spaces)
        if grep -q $'\t' "$file"; then
            echo -e "${YELLOW}⚠️  Tabs found in: $file (consider using spaces)${NC}"
        fi
    fi
    return 0
}

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo "No files staged for commit."
    exit 0
fi

# Check each staged file
for file in $STAGED_FILES; do
    # Skip if file doesn't exist (might be deleted)
    [ -f "$file" ] || continue
    
    # Check Python files
    if [[ "$file" == *.py ]]; then
        check_python_syntax "$file" || true  # Don't exit on error, continue checking
        check_python_issues "$file" || true  # Don't exit on error, continue checking
    fi
    
    # Check JSON files
    if [[ "$file" == *.json ]]; then
        check_json_syntax "$file" || true  # Don't exit on error, continue checking
    fi
done

# Summary
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All linting checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Linting failed with $ERRORS error(s)${NC}"
    echo -e "${YELLOW}Please fix the errors above before committing.${NC}"
    exit 1
fi
HOOK_EOF

chmod +x "$PRE_COMMIT_HOOK"

echo "✅ Git pre-commit hook installed successfully!"
echo "   Location: $PRE_COMMIT_HOOK"
echo ""
echo "The hook will now run automatically on every commit to check:"
echo "  - Python syntax errors"
echo "  - JSON validity"
echo "  - Common code quality issues (warnings)"