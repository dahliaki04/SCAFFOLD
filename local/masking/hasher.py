"""L1-16: SHA-256 Hasher.

Deterministic one-way hashing for PartName, SiteName, SupplierName.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache


@lru_cache(maxsize=65536)
def sha256_hash(value: str) -> str:
    """Return the SHA-256 hex digest of *value*.

    Always returns a 64-character lowercase hex string.
    Results are cached to avoid redundant computation for repeated values.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
