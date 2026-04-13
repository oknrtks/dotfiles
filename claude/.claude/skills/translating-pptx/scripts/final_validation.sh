#!/bin/bash
# Final Validation Script for Translated PPTX
# Performs comprehensive validation of the translated PowerPoint file

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to print info
info_msg() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    error_exit "Usage: $0 <output.pptx>"
fi

OUTPUT_PPTX="$1"

# Check if file exists
if [ ! -f "$OUTPUT_PPTX" ]; then
    error_exit "File not found: $OUTPUT_PPTX"
fi

echo "================================"
echo "Final Validation of Translated PPTX"
echo "================================"
echo ""
info_msg "File: $OUTPUT_PPTX"
echo ""

# Detect Python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error_exit "Python not found"
fi

# Step 1: File integrity check
echo "Step 1: File Integrity Check"
echo "----------------------------"

# Check if it's a valid PPTX file (should be a ZIP file)
if ! file "$OUTPUT_PPTX" | grep -q "Zip archive"; then
    error_exit "File is not a valid PPTX (ZIP) archive"
fi

success_msg "Valid PPTX file format"
echo ""

# Step 2: Check file size
echo "Step 2: File Size Check"
echo "----------------------------"

FILE_SIZE=$(stat -f%z "$OUTPUT_PPTX" 2>/dev/null || stat -c%s "$OUTPUT_PPTX" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)

info_msg "File size: ${FILE_SIZE_MB} MB"

if (( $(echo "$FILE_SIZE_MB < 0.1" | bc -l) )); then
    warning_msg "File size seems too small (< 0.1 MB)"
elif (( $(echo "$FILE_SIZE_MB > 100" | bc -l) )); then
    warning_msg "File size seems very large (> 100 MB)"
else
    success_msg "File size is reasonable"
fi
echo ""

# Step 3: Japanese text detection
echo "Step 3: Japanese Text Detection"
echo "----------------------------"

# Try to extract text and check for Japanese
if command -v markitdown &> /dev/null || $PYTHON_CMD -c "import markitdown" 2> /dev/null; then
    info_msg "Extracting text from PPTX..."

    # Create temporary file for text extraction
    TEMP_TEXT=$(mktemp)

    # Extract text using markitdown
    if $PYTHON_CMD -m markitdown "$OUTPUT_PPTX" > "$TEMP_TEXT" 2>/dev/null; then
        # Check for Japanese characters (excluding image references)
        JAPANESE_LINES=$($PYTHON_CMD -c "
import sys
import re
japanese = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
count = 0
for line in open('$TEMP_TEXT', 'r', encoding='utf-8'):
    if japanese.search(line) and '.jpg' not in line and '.png' not in line:
        count += 1
        if count <= 5:
            print(f'{line.strip()[:80]}')
print(f'Total: {count}')
")

        TOTAL_JAPANESE=$(echo "$JAPANESE_LINES" | tail -1 | grep -o '[0-9]*' | head -1)

        if [ -n "$TOTAL_JAPANESE" ] && [ "$TOTAL_JAPANESE" -gt 0 ]; then
            warning_msg "Found $TOTAL_JAPANESE line(s) with Japanese text"
            echo ""
            echo "Sample lines with Japanese:"
            echo "$JAPANESE_LINES" | grep -v "total:" | head -5
            echo ""
            echo "Note: This may include proper nouns or technical terms"
        else
            success_msg "No Japanese text detected (except images)"
        fi
    else
        warning_msg "Could not extract text using markitdown"
    fi

    rm -f "$TEMP_TEXT"
else
    warning_msg "markitdown not available for text extraction"
fi
echo ""

# Step 4: Check for color marking
echo "Step 4: Color Marking Check"
echo "----------------------------"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)

# Unpack PPTX
unzip -q "$OUTPUT_PPTX" -d "$TEMP_DIR" 2>/dev/null || error_exit "Could not unpack PPTX file"

# Check for purple color marking (RGB:128,0,128 = hex 800080)
SLIDE_XML_FILES=$(find "$TEMP_DIR/ppt/slides" -name "*.xml" 2>/dev/null || true)

if [ -n "$SLIDE_XML_FILES" ]; then
    PURPLE_COUNT=$(grep -r "800080" "$TEMP_DIR/ppt/slides" 2>/dev/null | wc -l || echo "0")

    if [ "$PURPLE_COUNT" -gt 0 ]; then
        success_msg "Found purple color marking (RGB:128,0,128) in $PURPLE_COUNT location(s)"
    else
        warning_msg "No purple color marking detected"
        info_msg "Translations may not have color marking applied"
    fi
else
    warning_msg "Could not check for color marking (slides not found)"
fi

# Clean up
rm -rf "$TEMP_DIR"
echo ""

# Step 5: Generate validation report
echo "Step 5: Validation Summary"
echo "----------------------------"

# Create validation report file
REPORT_FILE="validation_report.txt"

{
    echo "================================"
    echo "Translation Validation Report"
    echo "================================"
    echo ""
    echo "File: $OUTPUT_PPTX"
    echo "Size: ${FILE_SIZE_MB} MB"
    echo "Date: $(date)"
    echo ""
    echo "Checks Performed:"
    echo "  ✓ File integrity: Valid PPTX format"
    echo "  ✓ File size: ${FILE_SIZE_MB} MB"
    echo "  ✓ Japanese text detection: Completed"
    echo "  ✓ Color marking check: Completed"
    echo ""
    echo "Recommendations:"
    echo "  1. Open the file in PowerPoint or compatible viewer"
    echo "  2. Visually inspect layout and formatting"
    echo "  3. Check that translations are readable and accurate"
    echo "  4. Verify color marking is applied correctly"
    echo "  5. Test presentation mode if applicable"
    echo ""
} > "$REPORT_FILE"

success_msg "Validation report saved to: $REPORT_FILE"
echo ""

# Final summary
echo "================================"
echo -e "${GREEN}Validation Complete!${NC}"
echo "================================"
echo ""
echo "Next Steps:"
echo "  1. Review validation report: cat $REPORT_FILE"
echo "  2. Open file in PowerPoint: $OUTPUT_PPTX"
echo "  3. Verify visually:"
echo "     - Layout is preserved"
echo "     - Text is readable"
echo "     - Color marking is visible"
echo "     - No formatting issues"
echo ""
