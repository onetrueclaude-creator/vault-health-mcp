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
    parser.add_argument("--license-key", default=None,
                        help="Pro license key (JWT). Overrides VAULT_HEALTH_LICENSE env var and ~/.vault-health-mcp/license.jwt")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    from .license import load_license
    license = load_license(args.license_key)

    from .server import mcp_server, init, set_license
    set_license(license)

    if args.vault:
        vault_path = os.path.expanduser(args.vault)
        if not os.path.isdir(vault_path):
            print(f"Error: vault path does not exist: {vault_path}", file=sys.stderr)
            sys.exit(1)
        init(vault_path)
        print(f"vault-health-mcp: serving {vault_path}", file=sys.stderr)
    else:
        print("vault-health-mcp: starting without vault (use configure_vault tool to set path)", file=sys.stderr)

    if license:
        print(f"vault-health-mcp: Pro license active (plan={license.plan}, sub={license.subject})",
              file=sys.stderr)

    if args.transport == "streamable-http":
        port = int(os.environ.get("PORT") or args.port)
        mcp_server.settings.host = "0.0.0.0"
        mcp_server.settings.port = port
        mcp_server.settings.stateless_http = True
        print(f"vault-health-mcp: binding streamable-http on 0.0.0.0:{port} (stateless)", file=sys.stderr)

    mcp_server.run(transport=args.transport)


if __name__ == "__main__":
    main()
