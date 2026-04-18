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

| Tool | Description |
|------|-------------|
| `check_vault_health` | Full structural scan: broken links, orphans, missing frontmatter |
| `repair_vault` | Auto-fix safe issues (add-only, never deletes) |
| `vault_statistics` | File count, link count, orphan %, frontmatter coverage |
| `find_orphans` | List all structurally disconnected leaf notes |
| `find_broken_links` | List all wikilinks pointing to non-existent files |

## How auto-repair works

`repair_vault` only makes **additive** changes:
- Broken `[[links]]` → replaced with plain text (the link text is preserved)
- Missing frontmatter → adds a default YAML block with title and type

It never deletes files, removes content, or modifies existing frontmatter values.

## Requirements

- Python 3.10+
- An Obsidian vault (any size)

## License

MIT
