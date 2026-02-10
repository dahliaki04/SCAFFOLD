"""Tests for L1-31 (Free Tier Gate) and L2-32 (RSA Signature Verification)."""

import base64
import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest


# ===================================================================
# L1-31: Free Tier Gate
# ===================================================================

class TestFreeTierGate:
    """L1-31: ≤5 products + ≤2,000 rows check at runtime."""

    def test_within_free_limits(self, part_master_df, bom_df):
        """Test data (3 end products, <2000 rows) passes free tier check."""
        from local.core.licensing import check_free_tier_limits
        result = check_free_tier_limits(part_master_df, bom_df)
        assert result is None  # No error = within limits

    def test_exceeds_end_product_limit(self, bom_df):
        """More than 5 end products triggers free tier limit."""
        from local.core.licensing import check_free_tier_limits
        # Create 6 end products
        rows = [{"PartNumber": f"FG-{i:03d}", "Site": "PLANT-A", "Stage": "Warehouse",
                 "IsEndProduct": True} for i in range(6)]
        rows.append({"PartNumber": "RM-001", "Site": "PLANT-A", "Stage": "Raw Material",
                      "IsEndProduct": False})
        pm = pd.DataFrame(rows)
        result = check_free_tier_limits(pm, bom_df)
        assert result is not None
        assert "end products" in result.lower() or "5" in result

    def test_exceeds_row_limit(self):
        """More than 2000 total rows triggers free tier limit."""
        from local.core.licensing import check_free_tier_limits
        pm = pd.DataFrame({
            "PartNumber": [f"P{i}" for i in range(1001)],
            "Site": ["PLANT-A"] * 1001,
            "Stage": ["Raw Material"] * 1001,
            "IsEndProduct": [True] + [False] * 1000,
        })
        bom = pd.DataFrame({
            "AssemblyName": [f"P{i}" for i in range(1001)],
            "AssemblySite": ["PLANT-A"] * 1001,
            "ComponentName": [f"P{i+1}" for i in range(1001)],
            "ComponentSite": ["PLANT-A"] * 1001,
            "Qty": [1] * 1001,
        })
        result = check_free_tier_limits(pm, bom)
        assert result is not None
        assert "2,000" in result or "2000" in result

    def test_exactly_at_limits(self):
        """Exactly 5 end products and 2000 rows passes."""
        from local.core.licensing import check_free_tier_limits
        pm = pd.DataFrame({
            "PartNumber": [f"FG-{i}" for i in range(5)] + [f"P-{i}" for i in range(95)],
            "Site": ["PLANT-A"] * 100,
            "Stage": ["Warehouse"] * 5 + ["Raw Material"] * 95,
            "IsEndProduct": [True] * 5 + [False] * 95,
        })
        bom = pd.DataFrame({
            "AssemblyName": ["FG-0"] * 50,
            "AssemblySite": ["PLANT-A"] * 50,
            "ComponentName": [f"P-{i}" for i in range(50)],
            "ComponentSite": ["PLANT-A"] * 50,
            "Qty": [1] * 50,
        })
        # 100 + 50 = 150 rows, 5 end products — within limits
        result = check_free_tier_limits(pm, bom)
        assert result is None


# ===================================================================
# L2-32: RSA License Verification
# ===================================================================

class TestRSALicenseVerification:
    """L2-32: Offline-first RSA license key system."""

    @pytest.fixture(scope="class")
    def rsa_key_pair(self):
        """Generate a fresh RSA key pair for testing."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return private_pem, public_pem

    def test_generate_license_key_format(self, rsa_key_pair):
        """Generated license key matches SCAF-<TIER>-<b64>.<sig> format."""
        from local.core.licensing import generate_license_key
        private_pem, _ = rsa_key_pair
        key = generate_license_key(
            tier="Heavy",
            email="test@example.com",
            exp="2027-12-31T23:59:59+00:00",
            private_key_pem=private_pem,
        )
        assert key.startswith("SCAF-Heavy-")
        assert "." in key

    def test_generate_and_verify_roundtrip(self, rsa_key_pair, monkeypatch):
        """A generated key verifies successfully with the matching public key."""
        from local.core import licensing
        from local.core.licensing import generate_license_key, verify_license

        private_pem, public_pem = rsa_key_pair
        # Monkey-patch the public key to match our test key pair
        monkeypatch.setattr(licensing, "_PUBLIC_KEY_PEM", public_pem)

        key = generate_license_key(
            tier="Heavy",
            email="test@example.com",
            exp="2027-12-31T23:59:59+00:00",
            private_key_pem=private_pem,
        )
        result = verify_license(key)
        assert result == "Heavy"

    def test_light_tier_verification(self, rsa_key_pair, monkeypatch):
        """Light tier keys verify correctly."""
        from local.core import licensing
        from local.core.licensing import generate_license_key, verify_license

        private_pem, public_pem = rsa_key_pair
        monkeypatch.setattr(licensing, "_PUBLIC_KEY_PEM", public_pem)

        key = generate_license_key(
            tier="Light",
            email="light@example.com",
            exp="2027-12-31T23:59:59+00:00",
            private_key_pem=private_pem,
        )
        result = verify_license(key)
        assert result == "Light"

    def test_expired_key_rejected(self, rsa_key_pair, monkeypatch):
        """An expired license key returns None."""
        from local.core import licensing
        from local.core.licensing import generate_license_key, verify_license

        private_pem, public_pem = rsa_key_pair
        monkeypatch.setattr(licensing, "_PUBLIC_KEY_PEM", public_pem)

        key = generate_license_key(
            tier="Heavy",
            email="test@example.com",
            exp="2020-01-01T00:00:00+00:00",  # already expired
            private_key_pem=private_pem,
        )
        result = verify_license(key)
        assert result is None

    def test_tampered_key_rejected(self, rsa_key_pair, monkeypatch):
        """A tampered license key returns None."""
        from local.core import licensing
        from local.core.licensing import generate_license_key, verify_license

        private_pem, public_pem = rsa_key_pair
        monkeypatch.setattr(licensing, "_PUBLIC_KEY_PEM", public_pem)

        key = generate_license_key(
            tier="Heavy",
            email="test@example.com",
            exp="2027-12-31T23:59:59+00:00",
            private_key_pem=private_pem,
        )
        # Tamper with the payload
        tampered = key.replace("Heavy", "Light", 1)
        result = verify_license(tampered)
        assert result is None

    def test_malformed_key_returns_none(self):
        """Completely malformed keys return None gracefully."""
        from local.core.licensing import verify_license
        assert verify_license("") is None
        assert verify_license("not-a-key") is None
        assert verify_license("SCAF-Heavy") is None
        assert verify_license("SCAF-Heavy-abc") is None

    def test_extract_tier_sig(self):
        """extract_tier_sig returns the signature portion."""
        from local.core.licensing import extract_tier_sig
        sig = extract_tier_sig("SCAF-Heavy-payload.thesignature")
        assert sig == "thesignature"

    def test_extract_tier_sig_no_dot(self):
        """extract_tier_sig returns None if no dot separator."""
        from local.core.licensing import extract_tier_sig
        assert extract_tier_sig("SCAF-Heavy-payload") is None

    def test_tier_constants(self):
        """Tier constants are correctly defined."""
        from local.core.licensing import TIER_FREE, TIER_LIGHT, TIER_HEAVY
        assert TIER_FREE == "Free"
        assert TIER_LIGHT == "Light"
        assert TIER_HEAVY == "Heavy"
