"""Vault Health MCP Server — structural integrity for Obsidian vaults."""
import json
import os
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from .checker import check_health, auto_repair, vault_stats, scan_vault

_vault_path: str = ""

mcp_server = FastMCP(
    "vault-health",
    instructions="Structural health checker for Obsidian vaults. Finds broken wikilinks, "
    "orphaned notes, and missing frontmatter. Can auto-repair safe issues. "
    "Works with any Obsidian vault — no plugins required. "
    "If the server starts without a vault path, use the configure_vault tool first.",
)


@mcp_server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


def init(vault_path: str):
    global _vault_path
    _vault_path = vault_path


def _not_ready() -> str:
    return json.dumps({
        "error": "No vault configured. Use the configure_vault tool first to point the server at your Obsidian vault.",
        "hint": "Call configure_vault with the absolute path to your vault directory.",
    })


@mcp_server.tool(name="configure_vault", annotations={"readOnlyHint": False})
def tool_configure(vault_path: str) -> str:
    """Configure the vault path for this server. Call this first if the server
    started without a --vault argument."""
    if not os.path.isdir(vault_path):
        return json.dumps({"error": f"Directory does not exist: {vault_path}"})
    init(vault_path)
    stats = vault_stats(vault_path)
    return json.dumps({
        "status": "configured",
        "vault_path": vault_path,
        **stats,
    }, indent=2)


@mcp_server.tool(name="check_vault_health", annotations={"readOnlyHint": True})
def tool_check_health() -> str:
    """Scan the vault for structural issues: broken wikilinks, orphaned notes,
    missing frontmatter. Returns a categorized list of all issues found."""
    if not _vault_path:
        return _not_ready()
    issues = check_health(_vault_path)
    warning = [i for i in issues if i["severity"] == "warning"]
    info = [i for i in issues if i["severity"] == "info"]
    return json.dumps({
        "total": len(issues),
        "warnings": len(warning),
        "info": len(info),
        "issues": issues,
    }, indent=2)


@mcp_server.tool(name="repair_vault", annotations={"readOnlyHint": False, "destructiveHint": False})
def tool_repair(fix_broken_links: bool = True, fix_frontmatter: bool = True) -> str:
    """Auto-repair safe structural issues. Only adds content (frontmatter, plain text
    replacements for broken links). Never deletes files or content."""
    if not _vault_path:
        return _not_ready()
    issues = check_health(_vault_path)
    repairable = []
    if fix_broken_links:
        repairable.extend([i for i in issues if i["type"] == "broken_link"])
    if fix_frontmatter:
        repairable.extend([i for i in issues if i["type"] == "missing_frontmatter"])
    fixes = auto_repair(_vault_path, repairable)
    post_issues = check_health(_vault_path)
    return json.dumps({
        "fixes_applied": len(fixes),
        "fixes": fixes,
        "issues_before": len(issues),
        "issues_after": len(post_issues),
    }, indent=2)


@mcp_server.tool(name="vault_statistics", annotations={"readOnlyHint": True})
def tool_stats() -> str:
    """Vault-level analytics: file count, link count, orphans, broken links,
    frontmatter coverage percentage."""
    if not _vault_path:
        return _not_ready()
    stats = vault_stats(_vault_path)
    return json.dumps(stats, indent=2)


@mcp_server.tool(name="find_orphans", annotations={"readOnlyHint": True})
def tool_orphans() -> str:
    """Find all orphaned leaf notes — notes typed as 'leaf' in frontmatter that
    are not linked from any hub or branch file."""
    if not _vault_path:
        return _not_ready()
    issues = check_health(_vault_path)
    orphans = [i for i in issues if i["type"] == "orphaned_leaf"]
    return json.dumps({
        "orphan_count": len(orphans),
        "orphans": [{"file": o["file"]} for o in orphans],
    }, indent=2)


@mcp_server.tool(name="find_broken_links", annotations={"readOnlyHint": True})
def tool_broken() -> str:
    """Find all broken wikilinks — [[targets]] that don't resolve to any file
    in the vault. Excludes wikilinks inside code spans."""
    if not _vault_path:
        return _not_ready()
    issues = check_health(_vault_path)
    broken = [i for i in issues if i["type"] == "broken_link"]
    return json.dumps({
        "broken_count": len(broken),
        "broken_links": [{"file": b["file"], "target": b["detail"]} for b in broken],
    }, indent=2)
