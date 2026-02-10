"""L1-17: Stage Masking (S1/S2/S3...).

Replace real stage names with sequential IDs to hide industry fingerprint.
"""

from __future__ import annotations


def build_stage_map(stages: list[str]) -> dict[str, str]:
    """Build a mapping from real stage names to masked sequential IDs.

    ``stages`` should be an ordered list of unique stage names.
    Returns e.g. ``{"Warehouse": "S1", "Assembly": "S2", ...}``.
    """
    return {name: f"S{i + 1}" for i, name in enumerate(stages)}


def apply_stage_mask(value: str, stage_map: dict[str, str]) -> str:
    """Apply stage mask to a single value using the provided mapping."""
    return stage_map[value]
