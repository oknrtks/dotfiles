#!/bin/bash
# Environment Setup Script for translating-pptx Skill
# This script checks and installs required dependencies

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

# Detect Python
echo "Step 1: Detecting Python..."
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    success_msg "Found python3 (version $PYTHON_VERSION)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    success_msg "Found python (version $PYTHON_VERSION)"
else
    error_exit "Python not found. Please install Python 3.12+ first."
fi

# Check Python version
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    error_exit "Python 3.12+ required, but found $PYTHON_VERSION"
fi

success_msg "Python version is compatible: $PYTHON_VERSION"
echo ""

# Check if using uv
echo "Step 2: Checking package manager..."
if command -v uv &> /dev/null; then
    success_msg "Found uv package manager"
    PKG_MANAGER="uv"
    PKG_INSTALL="uv add"
    PKG_INSTALL_DEV="uv add --dev"
elif command -v pip3 &> /dev/null; then
    success_msg "Found pip3"
    PKG_MANAGER="pip"
    PKG_INSTALL="pip3 install"
    PKG_INSTALL_DEV="pip3 install"
elif command -v pip &> /dev/null; then
    success_msg "Found pip"
    PKG_MANAGER="pip"
    PKG_INSTALL="pip install"
    PKG_INSTALL_DEV="pip install"
else
    error_exit "No package manager found (uv, pip3, or pip)"
fi
echo ""

# Check and install python-pptx
echo "Step 3: Checking python-pptx..."
if $PYTHON_CMD -c "import pptx" 2> /dev/null; then
    PPTX_VERSION=$($PYTHON_CMD -c "import pptx; print(pptx.__version__)")
    success_msg "python-pptx is installed (version $PPTX_VERSION)"
else
    warning_msg "python-pptx not found. Installing..."
    $PKG_INSTALL "python-pptx"
    success_msg "python-pptx installed"
fi
echo ""

# Check and install markitdown
echo "Step 4: Checking markitdown..."
if $PYTHON_CMD -c "import markitdown" 2> /dev/null; then
    success_msg "markitdown is installed"
else
    warning_msg "markitdown not found. Installing..."
    $PKG_INSTALL '"markitdown[pptx]"'
    success_msg "markitdown installed"
fi
echo ""

# Check for jq
echo "Step 5: Checking jq..."
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

# Make scripts executable
echo "Step 6: Setting script permissions..."
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
for script in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$script" ]; then
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
echo "  Python: $PYTHON_CMD ($PYTHON_VERSION)"
echo "  Package Manager: $PKG_MANAGER"
echo "  Scripts Location: $SCRIPT_DIR"
echo ""
echo "Next Steps:"
echo "  1. Extract text: $PYTHON_CMD $SCRIPT_DIR/extract_texts_from_xml.py input.pptx extracted/"
echo "  2. Check translations: $PYTHON_CMD $SCRIPT_DIR/list_missing_translations.py"
echo "  3. Review translations: $PYTHON_CMD $SCRIPT_DIR/review_translations.py"
echo "  4. Verify: bash $SCRIPT_DIR/verify_translations.sh"
echo "  5. Apply: $PYTHON_CMD $SCRIPT_DIR/apply_translations.py input.pptx translations/ output.pptx"
echo "  6. Validate: bash $SCRIPT_DIR/final_validation.sh output.pptx"
echo ""
