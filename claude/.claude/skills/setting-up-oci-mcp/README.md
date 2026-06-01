# Setting Up OCI MCP Skill

This skill helps users set up Oracle Cloud Infrastructure (OCI) MCP servers for Claude Code.

## What This Skill Does

- Guides users through OCI MCP server setup using `claude mcp add` command
- Provides correct command syntax (prevents common mistakes)
- Explains authentication differences between SDK and CLI servers
- Includes troubleshooting for common issues

## When to Use

This skill is triggered when users:
- Want to configure OCI MCP servers
- Need help with `claude mcp add` command syntax
- Mention "OCI MCP", "oracle mcp", "setup oci"
- Experience authentication or connection issues

## Files

- **SKILL.md**: Main instructions and quick reference
- **TROUBLESHOOTING.md**: Common issues and solutions
- **command-examples.sh**: Copy-paste ready commands with explanations

## Key Features

### Correct Command Syntax

The skill emphasizes the correct `claude mcp add` syntax, which was a major pain point during development:

```bash
claude mcp add \
  -e OCI_CONFIG_PROFILE=DEFAULT \
  -e FASTMCP_LOG_LEVEL=ERROR \
  --scope user \
  oracle-oci-cloud-mcp-server -- uvx oracle.oci-cloud-mcp-server@latest
```

**Critical points:**
- Use `-e` (not `--env`)
- All options BEFORE server name
- `--` separator before command
- Run in separate terminal (not inside Claude Code)

### Two Server Types

**SDK Server (Recommended):**
- Uses OCI Python SDK directly
- Works with API Key authentication
- 317+ OCI clients available
- Easier to set up

**CLI Server (Optional):**
- Executes OCI CLI commands
- Requires security token authentication
- Useful for CLI-specific features

### Progressive Disclosure

- SKILL.md provides overview and common usage
- TROUBLESHOOTING.md has detailed error resolution
- command-examples.sh contains copy-paste ready commands

## Design Decisions

### Why Separate Terminal Emphasis?

The `claude mcp add` command modifies `~/.claude.json`, which is actively updated by Claude Code. Running it inside Claude Code causes file conflicts. This is emphasized throughout the skill.

### Why SDK Server as Default?

Based on real experience:
- API Key authentication is simpler than security tokens
- SDK server worked immediately after setup
- CLI server required additional token configuration
- Most use cases don't need CLI-specific features

### Why Include Command Examples Script?

Users can:
- Copy-paste exact commands without typos
- See syntax breakdown with comments
- Verify prerequisites before attempting setup
- Access common variations (different profiles, debug mode)

## Common User Journeys

### First-Time Setup

1. User mentions "setup OCI MCP"
2. Skill checks prerequisites (OCI CLI, uvx, config)
3. Provides SDK server setup command
4. Verifies connection
5. Tests with simple query

### Troubleshooting

1. User reports authentication error
2. Skill identifies error type from message
3. Points to specific TROUBLESHOOTING.md section
4. Provides fix command
5. Verifies resolution

### Command Syntax Help

1. User gets "invalid environment variable" error
2. Skill explains common syntax mistakes
3. Provides correct command format
4. Shows command breakdown

## Testing Recommendations

Test this skill by asking:
- "How do I set up OCI MCP servers?"
- "I'm getting an authentication error with OCI MCP"
- "What's the correct syntax for claude mcp add?"
- "Why can't I run claude mcp add inside Claude Code?"

## Future Enhancements

Potential additions:
- Security token setup workflow for CLI server
- Multi-profile configuration examples
- OCI resource query examples
- Integration with oci-design-query skill

## Related Skills

- **oci-design-query**: Query OCI design documents after MCP is set up
- **mcp-builder**: Build custom MCP servers
