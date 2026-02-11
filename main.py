#!/usr/bin/env python3
"""SCAFFOLD Local Tool — Entry point.

When run without arguments, launches the GUI (L1-32).
When run with CLI arguments, runs the command-line pipeline.

This file is also the PyInstaller entry point (L1-33).
"""

import sys


def main() -> None:
    if len(sys.argv) > 1:
        # CLI mode — delegate to cli.main()
        from local.cli import main as cli_main
        cli_main()
    else:
        # GUI mode — launch ttkbootstrap interface
        from local.gui.app import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
