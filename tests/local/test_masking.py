"""Tests for L1-16 (SHA-256 Hasher), L1-17 (Stage Masking), L1-18 (Jitter Engine)."""

import pytest


# ===================================================================
# L1-16: SHA-256 Hasher
# ===================================================================

class TestSHA256Hasher:
    """L1-16: Hash PartName, SiteName, SupplierName."""

    def test_hash_deterministic(self):
        """Same input always produces the same hash."""
        from local.masking.hasher import sha256_hash
        assert sha256_hash("FG-001") == sha256_hash("FG-001")

    def test_hash_different_inputs(self):
        """Different inputs produce different hashes."""
        from local.masking.hasher import sha256_hash
        assert sha256_hash("FG-001") != sha256_hash("FG-002")

    def test_hash_is_hex_string(self):
        """Hash output is a 64-char hex string (SHA-256)."""
        from local.masking.hasher import sha256_hash
        h = sha256_hash("FG-001")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_not_reversible(self):
        """Hash doesn't contain original value."""
        from local.masking.hasher import sha256_hash
        h = sha256_hash("FG-001")
        assert "FG-001" not in h

    def test_hash_part_names(self, part_master_df):
        """All part names can be hashed without error."""
        from local.masking.hasher import sha256_hash
        for name in part_master_df["PartNumber"].unique():
            h = sha256_hash(name)
            assert len(h) == 64

    def test_hash_site_names(self, part_master_df):
        """All site names can be hashed without error."""
        from local.masking.hasher import sha256_hash
        for name in part_master_df["Site"].unique():
            h = sha256_hash(name)
            assert len(h) == 64

    def test_hash_supplier_names(self, supplier_map_df):
        """All supplier names can be hashed without error."""
        from local.masking.hasher import sha256_hash
        for name in supplier_map_df["Supplier"].unique():
            h = sha256_hash(name)
            assert len(h) == 64


# ===================================================================
# L1-17: Stage Masking (S1/S2/S3...)
# ===================================================================

class TestStageMasking:
    """L1-17: Replace real stage names with sequential IDs."""

    def test_stage_mapping_sequential(self):
        """Stage names mapped to S1, S2, S3... in order."""
        from local.masking.stage import build_stage_map
        stages = ["Warehouse", "Assembly", "Final Test"]
        smap = build_stage_map(stages)
        assert smap["Warehouse"] == "S1"
        assert smap["Assembly"] == "S2"
        assert smap["Final Test"] == "S3"

    def test_stage_mapping_deterministic(self):
        """Same input order → same mapping."""
        from local.masking.stage import build_stage_map
        stages = ["X", "Y", "Z"]
        smap1 = build_stage_map(stages)
        smap2 = build_stage_map(stages)
        assert smap1 == smap2

    def test_stage_mapping_unique_ids(self):
        """No two stages share the same masked ID."""
        from local.masking.stage import build_stage_map
        stages = ["Alpha", "Beta", "Gamma", "Delta", "Echo"]
        smap = build_stage_map(stages)
        assert len(set(smap.values())) == 5

    def test_stage_mapping_hides_names(self):
        """Masked IDs don't contain original stage names."""
        from local.masking.stage import build_stage_map
        stages = ["Warehouse", "Assembly"]
        smap = build_stage_map(stages)
        for masked in smap.values():
            assert "Warehouse" not in masked
            assert "Assembly" not in masked

    def test_apply_stage_mask(self):
        """Stage mask applied to a value produces masked output."""
        from local.masking.stage import build_stage_map, apply_stage_mask
        stages = ["Raw", "WIP", "FG"]
        smap = build_stage_map(stages)
        assert apply_stage_mask("WIP", smap) == "S2"

    def test_empty_stages(self):
        """Empty stage list produces empty mapping."""
        from local.masking.stage import build_stage_map
        smap = build_stage_map([])
        assert smap == {}


# ===================================================================
# L1-18: Jitter Engine (±15%)
# ===================================================================

class TestJitterEngine:
    """L1-18: Noise ≠ 0, floor ±3, max(1, result)."""

    def test_jitter_changes_value(self):
        """Jittered value differs from original."""
        from local.masking.jitter import apply_jitter
        # Run 100 times — every single one must differ
        original = 100
        for _ in range(100):
            assert apply_jitter(original) != original

    def test_jitter_never_zero_noise(self):
        """Noise is never zero (value always changes)."""
        from local.masking.jitter import apply_jitter
        for val in [1, 5, 10, 50, 100, 1000]:
            for _ in range(50):
                assert apply_jitter(val) != val

    def test_jitter_minimum_result_is_one(self):
        """Result is always >= 1."""
        from local.masking.jitter import apply_jitter
        for _ in range(100):
            assert apply_jitter(1) >= 1

    def test_jitter_floor_three(self):
        """For small values, jitter range is at least ±3."""
        from local.masking.jitter import apply_jitter
        # Value of 10 → 15% = 1.5 → floor to ±3
        results = {apply_jitter(10) for _ in range(500)}
        # Should have values at least 3 away from 10
        assert any(r <= 7 for r in results), "Should reach 10-3=7 or lower"
        assert any(r >= 13 for r in results), "Should reach 10+3=13 or higher"

    def test_jitter_within_range(self):
        """Jittered value stays within ±15% (or ±3 floor) of original."""
        from local.masking.jitter import apply_jitter
        original = 100
        range_val = max(3, int(original * 0.15))  # = 15
        for _ in range(500):
            result = apply_jitter(original)
            diff = abs(result - original)
            assert 1 <= diff <= range_val, \
                f"Jitter {result} is {diff} away from {original}, expected 1-{range_val}"

    def test_jitter_large_value(self):
        """Large value (1000) gets ±15% = ±150 range."""
        from local.masking.jitter import apply_jitter
        original = 1000
        results = {apply_jitter(original) for _ in range(500)}
        # Should have reasonable spread
        assert max(results) - min(results) >= 100

    def test_jitter_distribution_not_biased(self):
        """Jitter produces both positive and negative noise."""
        from local.masking.jitter import apply_jitter
        original = 100
        results = [apply_jitter(original) for _ in range(500)]
        above = sum(1 for r in results if r > original)
        below = sum(1 for r in results if r < original)
        # Both directions should have significant representation
        assert above > 50, "Too few values above original"
        assert below > 50, "Too few values below original"
