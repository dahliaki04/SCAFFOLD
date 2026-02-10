"""L1-31: Free Tier Gate / L2-32: RSA Signature Verification.

Offline-first RSA license key system — zero network calls.

License key format:
    SCAF-<TIER>-<base64(JSON payload)>.<RSA-SHA256 signature>
    Payload: {"tier": "Light|Heavy", "exp": "ISO-8601", "email": "..."}

Tier gating:
    Free  — ≤5 end products + ≤2,000 total rows
    Light — Unlimited processing, generates upload.json
    Heavy — Unlimited processing, generates upload.json + key.scaf
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_FREE = "Free"
TIER_LIGHT = "Light"
TIER_HEAVY = "Heavy"

_FREE_MAX_END_PRODUCTS = 5
_FREE_MAX_ROWS = 2000

# RSA public key for license verification (PEM format).
# The corresponding private key is held server-side only (serverless signer).
# This is the SCAFFOLD distribution public key — embedded in the binary.
_PUBLIC_KEY_PEM = """\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z5mXkYq3VJrHPqSdS4v
8jRbFqGz0yTG6Xk+Nyv3KAJ3pQXFGh1JfKMUbOJjBWJhDe8G6KnNx4R2TvEKQiC
6xqPJFNJ9MtwNzuGDGx2gF0IjNTyVm1XCwRSg2cJuD1V0rSL3YvJBlWqfr4OPpUj
G4T0KhzsFJ8m4nLRbi4EzgyJmPkISJbEz8TfU1D3XGLwRNuXa0HjK0hO5qRiLwgW
k5XQ6L7jZsRFJn6Kz0C0jWelxPTqjFSmiAjGEHhKuPAf+BsPrBqHvB5NI3Pz5e6n
j3LXY8NVRS5T2pGFYwizOb9S9IuvNhb8TyxBJq3Cr2CWKTZ3NcKVJTl0kzlLReKN
7wIDAQAB
-----END PUBLIC KEY-----
"""


# ---------------------------------------------------------------------------
# L1-31: Free Tier Gate
# ---------------------------------------------------------------------------

def check_free_tier_limits(
    part_master_df: "pd.DataFrame",
    bom_df: "pd.DataFrame",
) -> str | None:
    """Check if the data exceeds Free tier limits.

    Returns an error message string if limits are exceeded,
    or ``None`` if the data fits within Free tier.

    Free tier limits:
    * ≤5 end products (IsEndProduct == True)
    * ≤2,000 total rows (Part Master + BOM + Supplier Map combined)
    """
    end_products = part_master_df[part_master_df["IsEndProduct"]].shape[0]
    if end_products > _FREE_MAX_END_PRODUCTS:
        return (
            f"Free tier allows ≤{_FREE_MAX_END_PRODUCTS} end products, "
            f"found {end_products}"
        )

    total_rows = len(part_master_df) + len(bom_df)
    if total_rows > _FREE_MAX_ROWS:
        return (
            f"Free tier allows ≤{_FREE_MAX_ROWS} total rows, "
            f"found {total_rows}"
        )

    return None


# ---------------------------------------------------------------------------
# L2-32: RSA Signature Verification
# ---------------------------------------------------------------------------

def _load_public_key():
    """Load the embedded RSA public key."""
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    return load_pem_public_key(_PUBLIC_KEY_PEM.encode("utf-8"))


def verify_license(license_key: str) -> str | None:
    """Verify an RSA-signed license key and return the tier.

    License format: ``SCAF-<TIER>-<base64(JSON)>.<signature>``

    Returns the tier string ("Light" or "Heavy") if valid,
    or ``None`` if the key is invalid, expired, or malformed.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    try:
        # Parse: SCAF-<tier>-<payload_b64>.<sig_b64>
        if not license_key.startswith("SCAF-"):
            return None

        # Split on last dot to separate signature
        dot_idx = license_key.rfind(".")
        if dot_idx < 0:
            return None

        body = license_key[:dot_idx]
        sig_b64 = license_key[dot_idx + 1:]

        # Parse body: SCAF-<tier>-<payload_b64>
        parts = body.split("-", 2)
        if len(parts) != 3 or parts[0] != "SCAF":
            return None

        tier_claim = parts[1]
        payload_b64 = parts[2]

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "==")
        payload = json.loads(payload_bytes)

        # Check tier
        tier = payload.get("tier")
        if tier not in (TIER_LIGHT, TIER_HEAVY):
            return None

        # Check tier consistency
        if tier_claim != tier:
            return None

        # Check expiration
        exp_str = payload.get("exp")
        if exp_str:
            exp = datetime.fromisoformat(exp_str)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return None

        # Verify RSA signature
        signature = base64.urlsafe_b64decode(sig_b64 + "==")
        public_key = _load_public_key()
        public_key.verify(
            signature,
            body.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        return tier

    except Exception:
        return None


def extract_tier_sig(license_key: str) -> str | None:
    """Extract the RSA signature portion from a license key.

    This signature is embedded in upload.json so the SaaS can
    verify the tier client-side without needing the full license key.
    """
    dot_idx = license_key.rfind(".")
    if dot_idx < 0:
        return None
    return license_key[dot_idx + 1:]


# ---------------------------------------------------------------------------
# Key generation utility (for server-side / offline signing)
# ---------------------------------------------------------------------------

def generate_license_key(
    tier: str,
    email: str,
    exp: str,
    private_key_pem: str,
) -> str:
    """Generate a signed license key (server-side utility).

    This function is used by the payment webhook / manual signing script.
    It is NOT called by the Local Tool at runtime.

    Args:
        tier: "Light" or "Heavy"
        email: Customer email
        exp: Expiration date (ISO-8601)
        private_key_pem: RSA private key in PEM format

    Returns:
        License key string: ``SCAF-<TIER>-<base64(JSON)>.<signature>``
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    payload = json.dumps({"tier": tier, "exp": exp, "email": email})
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    # Remove padding for cleaner URLs
    payload_b64 = payload_b64.rstrip("=")

    body = f"SCAF-{tier}-{payload_b64}"

    private_key = load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    signature = private_key.sign(
        body.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    return f"{body}.{sig_b64}"
