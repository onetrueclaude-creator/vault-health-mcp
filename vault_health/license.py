"""License-key validation for vault-health-mcp Pro features.

Offline verification using Ed25519-signed JWTs. No network calls, no phone-home.
The public verification key is embedded below; the private signing key is held
separately by the publisher and never ships with the package.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import jwt
    from cryptography.hazmat.primitives import serialization
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False


_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEArTH0PdPhy/v5o7RRVUyi54TKLap6nqdTUZvnS1L0m+k=
-----END PUBLIC KEY-----
"""

_ISSUER = "vault-health-mcp"
_ALGORITHM = "EdDSA"

_BUY_URL = "https://github.com/onetrueclaude-creator/vault-health-mcp#pro-tier"


@dataclass(frozen=True)
class License:
    subject: str
    plan: str
    features: frozenset[str]
    expires_at: int | None
    issued_at: int
    jti: str

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() >= self.expires_at

    def has_feature(self, name: str) -> bool:
        if self.is_expired:
            return False
        return name in self.features or "all" in self.features


def _load_license_string() -> str | None:
    env = os.environ.get("VAULT_HEALTH_LICENSE")
    if env:
        return env.strip()

    for candidate in (
        Path.home() / ".vault-health-mcp" / "license.jwt",
        Path.home() / ".config" / "vault-health-mcp" / "license.jwt",
    ):
        if candidate.is_file():
            content = candidate.read_text().strip()
            if content:
                return content
    return None


def load_license(explicit_key: str | None = None) -> License | None:
    if not _CRYPTO_AVAILABLE:
        return None

    token = explicit_key or _load_license_string()
    if not token:
        return None

    try:
        public_key = serialization.load_pem_public_key(_PUBLIC_KEY_PEM)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[_ALGORITHM],
            issuer=_ISSUER,
            options={"require": ["iss", "iat", "sub", "plan"]},
        )
    except jwt.ExpiredSignatureError:
        print(
            "vault-health-mcp: license expired — continuing in free mode. "
            f"Renew at {_BUY_URL}",
            file=sys.stderr,
        )
        return None
    except jwt.InvalidTokenError as exc:
        print(
            f"vault-health-mcp: license invalid ({exc}) — continuing in free mode.",
            file=sys.stderr,
        )
        return None
    except Exception as exc:  # pragma: no cover
        print(f"vault-health-mcp: license check error ({exc}) — continuing in free mode.",
              file=sys.stderr)
        return None

    features = payload.get("features") or []
    if payload.get("plan") in ("pro", "lifetime") and not features:
        features = ["all"]

    return License(
        subject=payload["sub"],
        plan=payload["plan"],
        features=frozenset(features),
        expires_at=payload.get("exp"),
        issued_at=payload["iat"],
        jti=payload.get("jti", ""),
    )


def require_feature_error(feature: str) -> dict:
    """Return a JSON-serializable dict to send as a tool error when a Pro
    feature is requested without a valid license."""
    return {
        "error": f"'{feature}' is a Pro feature",
        "hint": f"Get a license at {_BUY_URL}, then install via VAULT_HEALTH_LICENSE env var, "
                f"--license-key flag, or ~/.vault-health-mcp/license.jwt file.",
        "status": "license_required",
    }
