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
        noise = random.choice(
            [i for i in range(-range_val, range_val + 1) if i != 0]
        )
    return max(1, real_val + noise)
