#!/bin/bash
# Environment Setup Script for translating-pptx Skill
# UV-first approach: ensures uv is installed and initializes project environment

set -e

echo "================================"
echo "Translation Skill Environment Setup"
echo "================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print error and exit
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Function to print success
success_msg() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
warning_msg() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Step 1: Check if uv is installed
echo "Step 1: Checking for uv package manager..."
if ! command -v uv &> /dev/null; then
    echo ""
    error_exit "uv is not installed. Please install uv first:

    curl -LsSf https://astral.sh/uv/install.sh | sh

    Or visit: https://docs.astral.sh/uv/getting-started/installation/

    This skill requires uv to avoid polluting your global Python environment."
fi

UV_VERSION=$(uv --version 2>&1 | awk '{print $2}')
success_msg "Found uv (version $UV_VERSION)"
echo ""

# Step 2: Check if we're in a uv project (pyproject.toml exists)
echo "Step 2: Checking for uv project..."
if [ ! -f "pyproject.toml" ] && [ ! -f "uv.lock" ]; then
    warning_msg "No uv project found (pyproject.toml missing)"
    echo ""
    echo "Initializing uv project in current directory..."
    uv init --no-readme
    success_msg "Created pyproject.toml and initialized uv project"
else
    success_msg "Found existing uv project"
fi
echo ""

# Step 3: Add required dependencies
echo "Step 3: Installing dependencies..."

# Check if python-pptx is in dependencies
if uv pip list 2>/dev/null | grep -q "python-pptx"; then
    success_msg "python-pptx is already installed"
else
    warning_msg "Adding python-pptx..."
    uv add python-pptx
    success_msg "python-pptx added"
fi

# Check if markitdown is in dependencies
if uv pip list 2>/dev/null | grep -q "markitdown"; then
    success_msg "markitdown is already installed"
else
    warning_msg "Adding markitdown with pptx support..."
    uv add 'markitdown[pptx]'
    success_msg "markitdown added"
fi
echo ""

# Step 4: Check for jq (system dependency)
echo "Step 4: Checking jq..."
if command -v jq &> /dev/null; then
    success_msg "jq is installed"
else
    warning_msg "jq not found. Please install jq:"
    echo "  - macOS: brew install jq"
    echo "  - Ubuntu/Debian: sudo apt-get install jq"
    echo "  - CentOS/RHEL: sudo yum install jq"
    error_exit "jq is required for this skill"
fi
echo ""

# Step 5: Make scripts executable
echo "Step 5: Setting script permissions..."
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
for script in "$SCRIPT_DIR"/*.py; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        success_msg "Made $(basename "$script") executable"
    fi
done
for script in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$script" ] && [ "$script" != "${BASH_SOURCE[0]}" ]; then
        chmod +x "$script"
        success_msg "Made $(basename "$script") executable"
    fi
done
echo ""

# Summary
echo "================================"
echo -e "${GREEN}Environment Setup Complete!${NC}"
echo "================================"
echo ""
echo "Environment Summary:"
echo "  Package Manager: uv ($UV_VERSION)"
echo "  Project: $(pwd)"
echo "  Python: uv managed (use 'uv run python')"
echo "  Scripts Location: $SCRIPT_DIR"
echo ""
echo "Next Steps:"
echo "  1. Extract text: uv run python $SCRIPT_DIR/extract_texts_from_xml.py input.pptx extracted/"
echo "  2. Check translations: uv run python $SCRIPT_DIR/list_missing_translations.py"
echo "  3. Create prompts: uv run python $SCRIPT_DIR/translate_missing.py <slide_num>"
echo "  4. Add translations: uv run python $SCRIPT_DIR/add_translations.py <slide_num> batch_file <json_file>"
echo "  5. Verify: bash $SCRIPT_DIR/verify_translations.sh"
echo "  6. Apply: uv run python $SCRIPT_DIR/apply_translations.py input.pptx translations/ output.pptx"
echo ""
