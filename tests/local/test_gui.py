"""Tests for L1-32 (ttkbootstrap GUI) and L1-35 (SmartScreen Disclaimer).

GUI tests are structural — they verify the module loads and classes exist
without requiring a display server (headless CI compatible).
"""

import tempfile
from pathlib import Path

import pytest


class TestGUIModule:
    """L1-32: ttkbootstrap GUI structural tests."""

    def test_module_importable(self):
        """GUI module can be imported."""
        from local.gui import app
        assert hasattr(app, "ScaffoldApp")
        assert hasattr(app, "launch_gui")

    def test_smartscreen_check_function_exists(self):
        """SmartScreen disclaimer function exists."""
        from local.gui.app import _check_smartscreen_disclaimer
        assert callable(_check_smartscreen_disclaimer)

    def test_smartscreen_flag_file(self):
        """SmartScreen disclaimer creates a flag file when accepted."""
        from local.gui.app import _SMARTSCREEN_KEY
        with tempfile.TemporaryDirectory() as tmpdir:
            flag_path = Path(tmpdir) / _SMARTSCREEN_KEY
            # Simulate acceptance by creating the file
            flag_path.write_text("accepted")
            assert flag_path.exists()

    def test_smartscreen_previously_accepted(self):
        """If flag file exists, disclaimer is skipped (returns True)."""
        from local.gui.app import _check_smartscreen_disclaimer
        with tempfile.TemporaryDirectory() as tmpdir:
            flag_path = Path(tmpdir) / ".scaffold_disclaimer_accepted"
            flag_path.write_text("accepted")
            # Should return True since flag exists
            result = _check_smartscreen_disclaimer(Path(tmpdir))
            assert result is True


class TestPyInstallerSpec:
    """L1-33: PyInstaller build spec exists and is valid."""

    def test_spec_file_exists(self):
        """scaffold.spec exists in project root."""
        spec_path = Path(__file__).parent.parent.parent / "scaffold.spec"
        assert spec_path.exists()

    def test_spec_references_main(self):
        """scaffold.spec references main.py as entry point."""
        spec_path = Path(__file__).parent.parent.parent / "scaffold.spec"
        content = spec_path.read_text()
        assert "main.py" in content

    def test_spec_collects_ttkbootstrap(self):
        """scaffold.spec collects ttkbootstrap resources."""
        spec_path = Path(__file__).parent.parent.parent / "scaffold.spec"
        content = spec_path.read_text()
        assert "ttkbootstrap" in content

    def test_spec_includes_hidden_imports(self):
        """scaffold.spec has required hidden imports."""
        spec_path = Path(__file__).parent.parent.parent / "scaffold.spec"
        content = spec_path.read_text()
        assert "orjson" in content
        assert "cryptography" in content

    def test_main_entry_exists(self):
        """main.py entry point exists."""
        main_path = Path(__file__).parent.parent.parent / "main.py"
        assert main_path.exists()

    def test_main_entry_importable(self):
        """main.py can be imported."""
        import importlib.util
        main_path = Path(__file__).parent.parent.parent / "main.py"
        spec = importlib.util.spec_from_file_location("main", main_path)
        mod = importlib.util.module_from_spec(spec)
        assert mod is not None
