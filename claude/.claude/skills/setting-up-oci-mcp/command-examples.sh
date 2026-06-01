#!/bin/bash
# OCI MCP Server Setup - Command Examples
#
# This file contains copy-paste ready commands for setting up OCI MCP servers.
# Run these commands in a SEPARATE terminal (not inside Claude Code).

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

echo "=== Checking Prerequisites ==="

# Check OCI CLI
if command -v oci &> /dev/null; then
    echo "✓ OCI CLI installed: $(oci --version)"
else
    echo "✗ OCI CLI not found. Install with:"
    echo "  bash -c \"\$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)\""
    exit 1
fi

# Check uvx
if command -v uvx &> /dev/null; then
    echo "✓ uvx installed"
else
    echo "✗ uvx not found. Install with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check OCI config
if [ -f ~/.oci/config ]; then
    echo "✓ OCI config exists: ~/.oci/config"
else
    echo "✗ OCI config not found. Run 'oci setup config'"
    exit 1
fi

echo ""
echo "=== All prerequisites met ==="
echo ""

# =============================================================================
# ADD SDK SERVER (RECOMMENDED)
# =============================================================================

echo "=== Adding OCI Cloud MCP Server (SDK) ==="
echo ""
echo "This is the RECOMMENDED server. It uses OCI Python SDK and works with API Key authentication."
echo ""

# Uncomment to execute:
# claude mcp add \
#   -e OCI_CONFIG_PROFILE=DEFAULT \
#   -e FASTMCP_LOG_LEVEL=ERROR \
#   --scope user \
#   oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest

echo "To add SDK server, uncomment the command above or copy-paste:"
echo ""
echo "claude mcp add \\"
echo "  -e OCI_CONFIG_PROFILE=DEFAULT \\"
echo "  -e FASTMCP_LOG_LEVEL=ERROR \\"
echo "  --scope user \\"
echo "  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest"
echo ""

# =============================================================================
# ADD CLI SERVER (OPTIONAL)
# =============================================================================

echo "=== Adding OCI API MCP Server (CLI) - OPTIONAL ==="
echo ""
echo "This server uses OCI CLI commands and requires security token authentication."
echo "Only add this if you specifically need CLI-based operations."
echo ""

# Uncomment to execute:
# claude mcp add \
#   -e OCI_CONFIG_PROFILE=DEFAULT \
#   -e FASTMCP_LOG_LEVEL=ERROR \
#   --scope user \
#   oracle-oci-api-mcp-server -- uvx oracle.oci-api-mcp-server@latest

echo "To add CLI server, uncomment the command above or copy-paste:"
echo ""
echo "claude mcp add \\"
echo "  -e OCI_CONFIG_PROFILE=DEFAULT \\"
echo "  -e FASTMCP_LOG_LEVEL=ERROR \\"
echo "  --scope user \\"
echo "  oracle-oci-api-mcp-server -- uvx oracle.oci-api-mcp-server@latest"
echo ""

# =============================================================================
# VERIFICATION COMMANDS
# =============================================================================

echo "=== Verification Commands ==="
echo ""
echo "After adding servers, verify with:"
echo ""
echo "  claude mcp list"
echo ""
echo "Expected output:"
echo "  oracle-oci-cloud-mcp-server: uvx oracle.oci-cloud-mcp-server@latest - ✓ Connected"
echo ""
echo "To test inside Claude Code, ask:"
echo "  'List all available OCI regions'"
echo ""

# =============================================================================
# COMMON VARIATIONS
# =============================================================================

echo "=== Common Variations ==="
echo ""

echo "1. Use different OCI profile:"
echo ""
echo "claude mcp add \\"
echo "  -e OCI_CONFIG_PROFILE=MyProfile \\"
echo "  -e FASTMCP_LOG_LEVEL=ERROR \\"
echo "  --scope user \\"
echo "  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest"
echo ""

echo "2. Enable debug logging:"
echo ""
echo "claude mcp add \\"
echo "  -e OCI_CONFIG_PROFILE=DEFAULT \\"
echo "  -e FASTMCP_LOG_LEVEL=DEBUG \\"
echo "  --scope user \\"
echo "  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest"
echo ""

echo "3. Add to project scope only (shared with team):"
echo ""
echo "claude mcp add \\"
echo "  -e OCI_CONFIG_PROFILE=DEFAULT \\"
echo "  -e FASTMCP_LOG_LEVEL=ERROR \\"
echo "  --scope project \\"
echo "  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest"
echo ""

# =============================================================================
# MANAGEMENT COMMANDS
# =============================================================================

echo "=== Management Commands ==="
echo ""

echo "List all MCP servers:"
echo "  claude mcp list"
echo ""

echo "Get details of specific server:"
echo "  claude mcp get oracle-oci-cloud-mcp-server"
echo ""

echo "Remove a server:"
echo "  claude mcp remove oracle-oci-cloud-mcp-server"
echo ""

echo "Update server (remove and re-add):"
echo "  claude mcp remove oracle-oci-cloud-mcp-server"
echo "  claude mcp add -e OCI_CONFIG_PROFILE=DEFAULT --scope user oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest"
echo ""

# =============================================================================
# SYNTAX REFERENCE
# =============================================================================

echo "=== Command Syntax Reference ==="
echo ""
echo "General format:"
echo "  claude mcp add [options] <server-name> -- <command> [args...]"
echo ""
echo "Key points:"
echo "  - ALL options must come BEFORE server name"
echo "  - Use -e for environment variables (not --env)"
echo "  - Use -- to separate options from command"
echo "  - No spaces around = in -e KEY=VALUE"
echo ""
echo "Example breakdown:"
echo "  claude mcp add \\"
echo "    -e OCI_CONFIG_PROFILE=DEFAULT \\    # Environment variable"
echo "    -e FASTMCP_LOG_LEVEL=ERROR \\       # Another env variable"
echo "    --scope user \\                     # Scope option"
echo "    oracle-oci-cloud-mcp-server \\     # Server name"
echo "    -- \\                               # Separator"
echo "    uvx oracle.oci-cloud-mcp-server@latest  # Command and args"
echo ""
