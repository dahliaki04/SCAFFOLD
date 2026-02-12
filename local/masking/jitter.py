"""L1-18: Jitter Engine (±15%).

Adds non-zero noise to numeric values for masking.
Constraints: noise ≠ 0, floor ±3, result >= 1.
"""

from __future__ import annotations

import random


def apply_jitter(real_val: int) -> int:
    """Apply ±15% jitter to *real_val*.

    * Range is ``max(3, int(real_val * 0.15))`` — at least ±3.
    * Noise is **never** zero (value always changes).
    * Result is always ``>= 1``.
    """
    range_val = max(3, int(real_val * 0.15))
    # For small values where negative noise would clamp back to original,
    # restrict to positive-only noise to guarantee the value changes.
    if real_val <= range_val + 1:
        noise = random.randint(1, range_val)
    else:
        # Pick from [-range_val, range_val] excluding 0 without building a list.
        # There are 2*range_val valid choices; map [1, 2*range_val] to that set.
        raw = random.randint(1, 2 * range_val)
        noise = raw if raw <= range_val else -(raw - range_val)
    return max(1, real_val + noise)
