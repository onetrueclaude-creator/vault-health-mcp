"""CLI entry point for vault-health-mcp."""
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        prog="vault-health-mcp",
        description="MCP server for Obsidian vault structural health checks.",
    )
    parser.add_argument("--vault", "-v", default=None,
                        help="Path to Obsidian vault (optional — can be configured later via configure_vault tool)")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    from .server import mcp_server, init

    if args.vault:
        vault_path = os.path.expanduser(args.vault)
        if not os.path.isdir(vault_path):
            print(f"Error: vault path does not exist: {vault_path}", file=sys.stderr)
            sys.exit(1)
        init(vault_path)
        print(f"vault-health-mcp: serving {vault_path}", file=sys.stderr)
    else:
        print("vault-health-mcp: starting without vault (use configure_vault tool to set path)", file=sys.stderr)

    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()
