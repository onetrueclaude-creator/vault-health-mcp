"""Vault structural health checker — portable version for any Obsidian vault."""
import os
import re
import fnmatch
import yaml


WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

EXCLUDED_DEFAULT = [".obsidian/*", ".trash/*", "templates/*", ".hebbian/*"]


def _strip_code(text: str) -> str:
    text = CODE_FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    return text


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return {}


def scan_vault(vault_path: str, excluded: list[str] | None = None) -> dict:
    """Scan vault and return {stem: {path, rel, fm, links, content}}."""
    excluded = excluded or EXCLUDED_DEFAULT
    notes = {}
    for root, _, files in os.walk(vault_path):
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_path)
            if any(fnmatch.fnmatch(rel, p) for p in excluded):
                continue
            try:
                with open(full, encoding="utf-8") as fp:
                    content = fp.read()
            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                continue
            fm = _parse_frontmatter(content)
            cleaned = _strip_code(content)
            links = [m.strip().split("/")[-1].replace(".md", "")
                     for m in WIKILINK_RE.findall(cleaned)]
            stem = f.replace(".md", "")
            notes[stem] = {"path": full, "rel": rel, "fm": fm, "links": links, "content": content}
    return notes


def check_health(vault_path: str, excluded: list[str] | None = None) -> list[dict]:
    """Run all health checks, return list of issues."""
    notes = scan_vault(vault_path, excluded)
    issues = []

    # Build who-links-to-whom
    linked_from_hub = set()
    for stem, note in notes.items():
        ftype = note["fm"].get("type", "")
        if ftype in ("hub", "branch", "center"):
            for target in note["links"]:
                linked_from_hub.add(target)

    for stem, note in notes.items():
        # Broken wikilinks
        for target in note["links"]:
            if target not in notes:
                issues.append({
                    "file": note["rel"], "type": "broken_link",
                    "detail": f"[[{target}]] does not resolve",
                    "severity": "warning",
                })

        # Missing frontmatter
        if not note["fm"]:
            issues.append({
                "file": note["rel"], "type": "missing_frontmatter",
                "detail": "no YAML frontmatter found",
                "severity": "warning",
            })

        # Orphaned leaves
        ftype = note["fm"].get("type", "")
        if ftype == "leaf" and stem not in linked_from_hub:
            issues.append({
                "file": note["rel"], "type": "orphaned_leaf",
                "detail": "not linked from any hub or branch file",
                "severity": "info",
            })

    issues.sort(key=lambda i: ({"warning": 0, "info": 1}.get(i["severity"], 2), i["file"]))
    return issues


def auto_repair(vault_path: str, issues: list[dict]) -> list[dict]:
    """Auto-fix safe issues. Returns list of fixes applied."""
    fixes = []
    for issue in issues:
        if issue["type"] == "missing_frontmatter" and "no YAML frontmatter" in issue["detail"]:
            path = os.path.join(vault_path, issue["file"])
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError):
                continue
            stem = os.path.basename(issue["file"]).replace(".md", "")
            slug = re.sub(r"[^a-z0-9]+", stem.lower(), "-").strip("-")
            folder = issue["file"].split("/")[0] if "/" in issue["file"] else "notes"
            new_fm = f"---\ntitle: {stem}\ntype: leaf\ntags:\n  - {folder}\n---\n\n"
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_fm + content)
            fixes.append({"file": issue["file"], "action": "added default frontmatter"})

        elif issue["type"] == "broken_link":
            m = re.search(r"\[\[(.+?)\]\]", issue["detail"])
            if not m:
                continue
            target = m.group(1)
            path = os.path.join(vault_path, issue["file"])
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError):
                continue
            pattern = re.compile(r"\[\[" + re.escape(target) + r"(?:\|([^\]]+))?\]\]")
            match = pattern.search(content)
            if match:
                display = match.group(1) or target
                content = pattern.sub(display, content, count=1)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixes.append({"file": issue["file"], "action": f"replaced [[{target}]] with plain text"})

    return fixes


def vault_stats(vault_path: str, excluded: list[str] | None = None) -> dict:
    """Compute vault-level statistics."""
    notes = scan_vault(vault_path, excluded)
    total_links = sum(len(n["links"]) for n in notes.values())
    orphans = 0
    linked_from_hub = set()
    for stem, note in notes.items():
        if note["fm"].get("type") in ("hub", "branch", "center"):
            for t in note["links"]:
                linked_from_hub.add(t)
    for stem, note in notes.items():
        if note["fm"].get("type") == "leaf" and stem not in linked_from_hub:
            orphans += 1
    broken = sum(1 for n in notes.values() for t in n["links"] if t not in notes)

    return {
        "total_files": len(notes),
        "total_links": total_links,
        "orphan_count": orphans,
        "broken_link_count": broken,
        "avg_links_per_file": round(total_links / max(len(notes), 1), 2),
        "has_frontmatter_pct": round(100 * sum(1 for n in notes.values() if n["fm"]) / max(len(notes), 1)),
    }
