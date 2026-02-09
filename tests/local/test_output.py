"""Tests for L1-19 (upload.json Generator), L1-20 (key.scaf Generator), L1-21 (orjson Integration)."""

import json
import struct
import tempfile
from pathlib import Path

import pytest


# ===================================================================
# L1-19: upload.json Generator
# ===================================================================

class TestUploadJsonGenerator:
    """L1-19: SCAFFOLD standard JSON format (plaintext, all values masked)."""

    def test_upload_json_has_required_keys(self, digraph, part_master_df, supplier_map_df, end_products):
        """upload.json contains meta, nodes, edges, paths, risk."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        assert set(data.keys()) >= {"meta", "nodes", "edges", "paths", "risk"}

    def test_upload_json_meta_version(self, digraph, part_master_df, supplier_map_df, end_products):
        """Meta section contains version 3.0."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        assert data["meta"]["version"] == "3.0"

    def test_upload_json_meta_timestamp(self, digraph, part_master_df, supplier_map_df, end_products):
        """Meta section contains ISO-8601 timestamp."""
        from local.core.output import generate_upload_json
        from datetime import datetime
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        # Should parse as ISO-8601
        datetime.fromisoformat(data["meta"]["generated"])

    def test_upload_json_nodes_are_hashed(self, digraph, part_master_df, supplier_map_df, end_products):
        """Node IDs in upload.json are SHA-256 hashes, not plaintext."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        for node_id in data["nodes"]:
            # SHA-256 hex is 64 chars
            assert len(node_id) == 64, f"Node ID {node_id} doesn't look like SHA-256"
            assert all(c in "0123456789abcdef" for c in node_id)

    def test_upload_json_no_plaintext_parts(self, digraph, part_master_df, supplier_map_df, end_products):
        """upload.json contains zero human-readable part names."""
        from local.core.output import generate_upload_json
        import orjson
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        serialized = orjson.dumps(data).decode()
        for name in part_master_df["PartNumber"].unique():
            assert name not in serialized, f"Plaintext part name '{name}' found in upload.json"

    def test_upload_json_no_plaintext_sites(self, digraph, part_master_df, supplier_map_df, end_products):
        """upload.json contains zero human-readable site names."""
        from local.core.output import generate_upload_json
        import orjson
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        serialized = orjson.dumps(data).decode()
        for name in part_master_df["Site"].unique():
            assert name not in serialized, f"Plaintext site name '{name}' found in upload.json"

    def test_upload_json_stages_masked(self, digraph, part_master_df, supplier_map_df, end_products):
        """Stage values are S1, S2, S3... not real names."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        for node_data in data["nodes"].values():
            assert node_data["stage"].startswith("S"), \
                f"Stage '{node_data['stage']}' not masked"

    def test_upload_json_edges_structure(self, digraph, part_master_df, supplier_map_df, end_products):
        """Edges have parent, child, qty keys."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        assert len(data["edges"]) > 0
        for edge in data["edges"]:
            assert set(edge.keys()) >= {"parent", "child", "qty"}

    def test_upload_json_paths_for_each_fg(self, digraph, part_master_df, supplier_map_df, end_products):
        """Paths section has entries for each end product."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        assert len(data["paths"]) == 3  # 3 end products

    def test_upload_json_risk_section(self, digraph, part_master_df, supplier_map_df, end_products):
        """Risk section contains max_lt and depth for each node."""
        from local.core.output import generate_upload_json
        data = generate_upload_json(digraph, part_master_df, supplier_map_df, end_products)
        assert len(data["risk"]) > 0
        for risk_data in data["risk"].values():
            assert "max_lt" in risk_data
            assert "depth" in risk_data


# ===================================================================
# L1-20: key.scaf Generator (AES)
# ===================================================================

class TestKeyScafGenerator:
    """L1-20: MAGIC=b'SCAF' + VERSION + SALT + Fernet(PBKDF2(password))."""

    def test_keyscaf_magic_bytes(self):
        """key.scaf starts with b'SCAF' magic bytes."""
        from local.core.output import generate_key_scaf
        data = {"test": "value"}
        raw = generate_key_scaf(data, password="testpass123")
        assert raw[:4] == b"SCAF"

    def test_keyscaf_version(self):
        """key.scaf version field is 3 (uint16 LE)."""
        from local.core.output import generate_key_scaf
        data = {"test": "value"}
        raw = generate_key_scaf(data, password="testpass123")
        version = struct.unpack_from("<H", raw, 4)[0]
        assert version == 3

    def test_keyscaf_salt_length(self):
        """key.scaf contains 16-byte salt at bytes 6-22."""
        from local.core.output import generate_key_scaf
        data = {"test": "value"}
        raw = generate_key_scaf(data, password="testpass123")
        salt = raw[6:22]
        assert len(salt) == 16

    def test_keyscaf_salt_unique(self):
        """Each generation produces a different salt."""
        from local.core.output import generate_key_scaf
        data = {"test": "value"}
        raw1 = generate_key_scaf(data, password="testpass123")
        raw2 = generate_key_scaf(data, password="testpass123")
        assert raw1[6:22] != raw2[6:22]

    def test_keyscaf_roundtrip(self):
        """Encrypt then decrypt recovers original data."""
        from local.core.output import generate_key_scaf, decrypt_key_scaf
        data = {"parts": ["FG-001", "WIP-001"], "sites": ["PLANT-A"]}
        password = "s3cureP@ss!"
        raw = generate_key_scaf(data, password=password)
        recovered = decrypt_key_scaf(raw, password=password)
        assert recovered == data

    def test_keyscaf_wrong_password_fails(self):
        """Decryption with wrong password raises error."""
        from local.core.output import generate_key_scaf, decrypt_key_scaf
        data = {"test": "value"}
        raw = generate_key_scaf(data, password="correct")
        with pytest.raises(Exception):
            decrypt_key_scaf(raw, password="wrong")

    def test_keyscaf_fernet_token_present(self):
        """Bytes after salt contain a Fernet token (base64url)."""
        from local.core.output import generate_key_scaf
        data = {"test": "value"}
        raw = generate_key_scaf(data, password="testpass123")
        fernet_token = raw[22:]
        assert len(fernet_token) > 0
        # Fernet tokens are base64url encoded, starting with gAAAAA...
        # After zlib compression + encryption, should be non-trivial size

    def test_keyscaf_file_write_roundtrip(self):
        """Write to file and read back produces same data."""
        from local.core.output import generate_key_scaf, decrypt_key_scaf
        data = {"nodes": {"h1": {"stage": "S1"}}, "mapping": {"h1": "FG-001"}}
        password = "fileTest99"

        with tempfile.NamedTemporaryFile(suffix=".scaf", delete=False) as f:
            raw = generate_key_scaf(data, password=password)
            f.write(raw)
            f.flush()

            content = Path(f.name).read_bytes()
            recovered = decrypt_key_scaf(content, password=password)
            assert recovered == data


# ===================================================================
# L1-21: orjson Integration
# ===================================================================

class TestOrjsonIntegration:
    """L1-21: Replace stdlib json with orjson for 1M record perf."""

    def test_orjson_available(self):
        """orjson package is importable."""
        import orjson
        assert hasattr(orjson, "dumps")
        assert hasattr(orjson, "loads")

    def test_orjson_roundtrip(self):
        """orjson serializes and deserializes correctly."""
        import orjson
        data = {"nodes": {"abc123": {"stage": "S1", "lt": 42}}, "edges": []}
        raw = orjson.dumps(data)
        assert isinstance(raw, bytes)
        recovered = orjson.loads(raw)
        assert recovered == data

    def test_orjson_used_not_stdlib(self):
        """Output module uses orjson, not stdlib json."""
        import inspect
        from local.core import output
        source = inspect.getsource(output)
        assert "import orjson" in source or "from orjson" in source
        # Should not use stdlib json for serialization
        assert "json.dumps" not in source

    def test_orjson_handles_upload_json_structure(self):
        """orjson can serialize the full upload.json structure."""
        import orjson
        data = {
            "meta": {"version": "3.0", "generated": "2026-02-09T14:30:00"},
            "nodes": {f"hash_{i}": {"stage": f"S{i%6+1}", "lt": i*10, "depth": i%5}
                      for i in range(1000)},
            "edges": [{"parent": f"hash_{i}", "child": f"hash_{i+1}", "qty": i%10+1}
                      for i in range(999)],
            "paths": {f"hash_fg_{i}": [f"hash_{j}" for j in range(10)]
                      for i in range(5)},
            "risk": {f"hash_{i}": {"max_lt": i*10, "single_source": i%3==0, "depth": i%5}
                     for i in range(1000)},
        }
        raw = orjson.dumps(data)
        recovered = orjson.loads(raw)
        assert recovered["meta"]["version"] == "3.0"
        assert len(recovered["nodes"]) == 1000
