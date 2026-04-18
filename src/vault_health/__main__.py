"""CLI entry point for vault-health-mcp."""
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        prog="vault-health-mcp",
        description="MCP server for Obsidian vault structural health checks.",
    )
    parser.add_argument("--vault", "-v", required=True, help="Path to Obsidian vault")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    vault_path = os.path.expanduser(args.vault)
    if not os.path.isdir(vault_path):
        print(f"Error: vault path does not exist: {vault_path}", file=sys.stderr)
        sys.exit(1)

    from .server import mcp_server, init
    init(vault_path)
    print(f"vault-health-mcp: serving {vault_path}", file=sys.stderr)
    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()
