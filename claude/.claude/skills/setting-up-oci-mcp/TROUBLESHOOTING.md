# OCI MCP Troubleshooting

Common issues when setting up OCI MCP servers and their solutions.

## Authentication Errors

### "Config value for 'security_token_file' must be specified"

**Cause:** CLI server is trying to use security token authentication, but no token is configured.

**Solution 1: Use SDK server instead (recommended)**

The SDK server works with API Key authentication:

```bash
# Remove CLI server if added
claude mcp remove oracle-oci-api-mcp-server

# Use SDK server only
claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e FASTMCP_LOG_LEVEL=ERROR \
  --scope user \
  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

**Solution 2: Set up security token (for CLI server)**

```bash
# Authenticate with security token
oci session authenticate --region=ap-osaka-1 --tenancy-name=<your-tenancy-name>

# Follow browser prompts to complete authentication
# Token is saved to ~/.oci/<profile>_token
```

After authentication, the CLI server should work.

### "Invalid API key or signature"

**Cause:** API Key authentication is misconfigured.

**Check:**

```bash
# Verify config file exists and has correct permissions
ls -la ~/.oci/config
chmod 600 ~/.oci/config

# Verify private key exists
ls -la ~/.oci/oci_api_key.pem
chmod 600 ~/.oci/oci_api_key.pem

# Test OCI CLI directly
oci iam region list
```

If OCI CLI works but MCP server doesn't, check the `OCI_CONFIG_PROFILE` environment variable matches your profile name in `~/.oci/config`.

### "User not found" or "Tenancy not found"

**Cause:** OCIDs in config are incorrect or user/tenancy was deleted.

**Fix:**

1. Verify OCIDs in OCI Console:
   - User OCID: Identity → Users → (your user) → Copy OCID
   - Tenancy OCID: Profile menu → Tenancy → Copy OCID

2. Update `~/.oci/config`:

```ini
[DEFAULT]
user=<correct-user-ocid>
tenancy=<correct-tenancy-ocid>
fingerprint=<key-fingerprint>
region=ap-osaka-1
key_file=~/.oci/oci_api_key.pem
```

## Command Syntax Errors

### "Invalid environment variable format"

**Wrong:**

```bash
# --env option is not recognized
claude mcp add --env OCI_CONFIG_PROFILE=DEFAULT oracle-oci-cloud-mcp-server ...
```

**Correct:**

```bash
# Use -e (short form), not --env
claude mcp add -e OCI_CONFIG_PROFILE=DEFAULT oracle-oci-cloud-mcp-server ...
```

### "Unknown option '--command'"

**Wrong:**

```bash
# Old style syntax (doesn't work)
claude mcp add oracle-oci-cloud-mcp-server --command uvx --arg oracle.oci-cloud-mcp-server@latest
```

**Correct:**

```bash
# Use -- separator before command
claude mcp add oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

### Options appearing after server name

**Wrong:**

```bash
# Options after server name are treated as command arguments
claude mcp add oracle-oci-cloud-mcp-server -e OCI_CONFIG_PROFILE=DEFAULT ...
```

**Correct:**

```bash
# ALL options must come BEFORE server name
claude mcp add -e OCI_CONFIG_PROFILE=DEFAULT oracle-oci-cloud-mcp-server -- uvx ...
```

## Connection Issues

### "Failed to connect" in claude mcp list

**Check 1: uvx is available**

```bash
which uvx
# If not found:
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

**Check 2: Network access**

```bash
# Test uvx can download packages
uvx --version

# Test manually running the server
uvx oracle.oci-cloud-mcp-server@latest --version
```

**Check 3: Python environment**

```bash
# MCP servers need Python 3.8+
python3 --version
```

### MCP server not appearing in claude mcp list

**Cause 1: Configuration not saved**

```bash
# Check if server was added
claude mcp get oracle-oci-cloud-mcp-server

# If not found, re-add it
claude mcp add -e OCI_CONFIG_PROFILE=DEFAULT ...
```

**Cause 2: Wrong scope**

```bash
# If added with --scope project, it's only in current project
# Re-add with --scope user for global availability
claude mcp add --scope user -e OCI_CONFIG_PROFILE=DEFAULT ...
```

## .claude.json Editing Problems

### "File has been modified since read"

**Cause:** `.claude.json` is actively updated by Claude Code with conversation history.

**Solution:** Use `claude mcp add` command instead of manual editing.

**If manual edit is necessary:**

1. Exit Claude Code completely
2. Edit `~/.claude.json` with a text editor
3. Add to the root `mcpServers` object:

```json
{
  "mcpServers": {
    "oracle-oci-cloud-mcp-server": {
      "command": "uvx",
      "args": ["oracle.oci-cloud-mcp-server@latest"],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

4. Restart Claude Code

### Can't find mcpServers in .claude.json

`.claude.json` structure:

```json
{
  "projects": {
    "/path/to/project": {
      "mcpServers": {}  // Project-specific (local scope)
    }
  },
  "mcpServers": {  // Global user scope (add here)
    "oracle-oci-cloud-mcp-server": { ... }
  }
}
```

Add to the **root-level** `mcpServers`, not inside `projects`.

## OCI-Specific Issues

### "Compartment not found"

**Cause:** Using wrong compartment OCID or insufficient permissions.

**Check permissions:**

```bash
# List compartments you have access to
oci iam compartment list --compartment-id <tenancy-ocid>
```

Use the OCID from the output.

### "Region not subscribed"

**Cause:** Trying to access a region your tenancy isn't subscribed to.

**Check subscribed regions:**

```bash
oci iam region-subscription list --tenancy-id <tenancy-ocid>
```

Use a region from the output.

### Rate limiting errors

**Cause:** Too many API calls in short period.

**Solution:**

```bash
# Add retry configuration to environment
claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e OCI_SDK_RETRY_STRATEGY=default \
  --scope user \
  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

## Testing and Validation

### Verify SDK server is working

Inside Claude Code, ask:

```
List all available OCI regions
```

Expected: Claude uses `invoke_oci_api` with `oci.identity.IdentityClient.list_regions()`

### Verify CLI server is working

Inside Claude Code, ask:

```
Run OCI CLI command to list availability domains in my region
```

Expected: Claude uses `run_oci_command` with `oci iam availability-domain list`

### Check MCP server logs

```bash
# Get detailed logs by changing log level
claude mcp remove oracle-oci-cloud-mcp-server

claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e FASTMCP_LOG_LEVEL=DEBUG \
  --scope user \
  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

Logs appear in Claude Code's console output.

## Getting Help

If issues persist:

1. Check OCI CLI works directly: `oci iam region list`
2. Verify MCP server can run standalone: `uvx oracle.oci-cloud-mcp-server@latest --help`
3. Check Claude Code logs for error details
4. Review [Oracle MCP GitHub Issues](https://github.com/oracle/mcp/issues)

## Common Command Reference

```bash
# List all MCP servers
claude mcp list

# Get specific server details
claude mcp get oracle-oci-cloud-mcp-server

# Remove and re-add server
claude mcp remove oracle-oci-cloud-mcp-server
claude mcp add -e OCI_CONFIG_PROFILE=DEFAULT --scope user oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest

# Test OCI CLI directly
oci iam region list

# Test with different profile
claude mcp add -e OCI_CONFIG_PROFILE=MyProfile --scope user oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```
