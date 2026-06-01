---
name: setting-up-oci-mcp
description: Set up Oracle Cloud Infrastructure (OCI) MCP servers for Claude Code using the claude mcp add command. Use when the user wants to configure OCI MCP servers, add Oracle Cloud integration, or mentions "OCI MCP", "oracle mcp", "setup oci", or needs help with claude mcp add command syntax.
---

# Setting Up OCI MCP Servers

Oracle provides two official MCP servers for OCI integration:

| Server | Purpose | Authentication |
|--------|---------|----------------|
| **oracle-oci-cloud-mcp-server** | OCI Python SDK calls (recommended) | API Key |
| **oracle-oci-api-mcp-server** | OCI CLI command execution | Security Token |

**Use SDK server (oracle-oci-cloud-mcp-server) for most cases.** It works with API Key authentication and provides 317+ OCI clients.

## Prerequisites

Verify these are installed before proceeding:

```bash
# Check OCI CLI
oci --version

# Check uvx (from uv package manager)
uvx --version

# Check OCI config exists
ls ~/.oci/config
```

If missing:
- **OCI CLI**: `bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"`
- **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **OCI config**: Run `oci setup config` for API Key authentication

## Adding OCI MCP Servers

**CRITICAL: Run these commands in a SEPARATE terminal, NOT inside Claude Code.**

The `claude mcp add` command cannot run inside an active Claude Code session.

### Command Syntax Reference

The correct `claude mcp add` syntax for stdio servers:

```bash
claude mcp add \
  [options before name] \
  <server-name> -- <command> [args...]
```

**Options must come BEFORE the server name:**
- `-e KEY=VALUE` for environment variables (use `-e`, not `--env`)
- `--scope user|local|project` for scope
- `--transport stdio|http|sse` (stdio is default)

### Add SDK Server (Recommended)

```bash
claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e FASTMCP_LOG_LEVEL=ERROR \
  --scope user \
  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

This adds the SDK server globally (available in all projects).

### Add CLI Server (Optional)

```bash
claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e FASTMCP_LOG_LEVEL=ERROR \
  --scope user \
  oracle-oci-api-mcp-server -- uvx oracle.oci-api-mcp-server@latest
```

**Note:** CLI server requires security token authentication. See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for setup.

## Verification

After adding servers, verify they're working:

```bash
# List all MCP servers
claude mcp list

# Expected output includes:
# oracle-oci-cloud-mcp-server: uvx oracle.oci-cloud-mcp-server@latest - ✓ Connected
```

Inside Claude Code, test the SDK server:

```
List available OCI regions using the SDK server.
```

Claude will use `mcp__oracle-oci-cloud-mcp-server__invoke_oci_api` to call `oci.identity.IdentityClient.list_regions()`.

## Available Tools

### SDK Server (oracle-oci-cloud-mcp-server)

- `list_oci_clients`: List 317+ available OCI SDK clients
- `list_client_operations`: List operations for a specific client
- `describe_oci_operation`: Get detailed operation info (params, types)
- `invoke_oci_api`: Execute OCI SDK calls directly
- `find_oci_api`: Search for operations by keyword

**Example usage inside Claude Code:**

```
Show me all compartments in my OCI tenancy.
```

Claude will automatically:
1. Use `list_client_operations` to find `list_compartments`
2. Use `describe_oci_operation` to understand required params
3. Use `invoke_oci_api` to execute the call

### CLI Server (oracle-oci-api-mcp-server)

- `get_oci_command_help`: Get OCI CLI command help
- `run_oci_command`: Execute OCI CLI commands
- `resource://oci-api-commands`: Resource listing available commands

## Common Usage Patterns

### List Resources

```
List all compute instances in compartment <ocid>
```

### Get Resource Details

```
Show me details of instance <instance-ocid>
```

### Query Multiple Resources

```
List all VCNs and subnets in my tenancy
```

Claude will automatically use the appropriate MCP tools to fetch this information.

## Understanding Scopes

`--scope` determines where the MCP server configuration is stored:

- `user`: Global (all projects, stored in `~/.claude.json`)
- `local`: Current project only (stored in `~/.claude.json` under project path)
- `project`: Shared with team (stored in `.mcp.json` in project root)

**Recommendation:** Use `--scope user` for OCI servers since you'll use them across multiple projects.

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for:
- Authentication errors
- Security token setup
- Connection issues
- `.claude.json` editing problems

## Quick Reference

```bash
# List servers
claude mcp list

# Get server details
claude mcp get oracle-oci-cloud-mcp-server

# Remove server
claude mcp remove oracle-oci-cloud-mcp-server

# Test inside Claude Code
List available OCI regions
```

## Architecture Notes

**Why two servers?**

- **SDK server**: Direct Python SDK calls, more flexible, works with API Key
- **CLI server**: Uses OCI CLI, useful for CLI-specific features, requires security token

For most use cases, SDK server is sufficient and easier to set up.

**Why use separate terminal?**

The `claude mcp add` command modifies `~/.claude.json`, which is actively used by the running Claude Code session. Running it inside Claude Code causes conflicts.
