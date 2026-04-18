<!-- mcp-name: io.github.onetrueclaude-creator/vault-health-mcp -->

# vault-health-mcp

**MCP server for Obsidian vault structural health checks.**

Find broken wikilinks, orphaned notes, and missing frontmatter — then auto-repair them. Works with any Obsidian vault, no plugins required.

## Install

```bash
pip install vault-health-mcp
```

## Usage

### Claude Code
```bash
claude mcp add vault-health -- vault-health-mcp --vault ~/my-vault
```

### Claude Desktop
```json
{
  "mcpServers": {
    "vault-health": {
      "command": "uvx",
      "args": ["vault-health-mcp", "--vault", "/path/to/vault"]
    }
  }
}
```

## MCP Tools

| Tool | Tier | Description |
|------|------|-------------|
| `configure_vault` | Free | Point the server at a vault at runtime |
| `check_vault_health` | Free | Full structural scan: broken links, orphans, missing frontmatter |
| `find_orphans` | Free | List all structurally disconnected leaf notes |
| `find_broken_links` | Free | List all wikilinks pointing to non-existent files |
| `vault_statistics` | Free | File count, link count, orphan %, frontmatter coverage |
| `repair_vault` | **Pro** | Auto-fix safe issues (add-only, never deletes) |

## How auto-repair works (Pro)

`repair_vault` only makes **additive** changes:
- Broken `[[links]]` → replaced with plain text (the link text is preserved)
- Missing frontmatter → adds a default YAML block with title and type

It never deletes files, removes content, or modifies existing frontmatter values.

## Pro tier

The free tier detects every category of vault rot. The Pro tier unlocks `repair_vault` — one call to fix the safe categories automatically.

License activation — any one of these works:

```bash
# 1. Environment variable
export VAULT_HEALTH_LICENSE="eyJhbGc..."

# 2. CLI flag
vault-health-mcp --license-key "eyJhbGc..." --vault ~/my-vault

# 3. Config file
echo "eyJhbGc..." > ~/.vault-health-mcp/license.jwt
```

Licenses are verified fully offline — no phone-home, no activation server. Get a license: **[coming soon — Dodo Payments storefront in verification]**.

## Requirements

- Python 3.10+
- An Obsidian vault (any size)

## License

MIT
