"""L1-32: ttkbootstrap Desktop GUI / L1-35: SmartScreen Disclaimer.

Dark-mode desktop GUI for the SCAFFOLD Local Tool using ttkbootstrap
(darkly theme). Wraps the existing CLI pipeline in a graphical interface.

Features:
* File picker for Excel (.xlsx) or CSV inputs
* Password entry for key.scaf encryption
* License key entry for tier gating
* Export checkboxes (Kinaxis V7, Generic CSV)
* Output directory selector
* Progress log with real-time status
* SmartScreen first-run disclaimer (L1-35)
"""

from __future__ import annotations

import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

# ttkbootstrap may not be installed in all environments (CI/headless).
# Guard the import so the module can still be tested for structure.
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.dialogs import Messagebox
    _HAS_TTK = True
except ImportError:
    _HAS_TTK = False


_SMARTSCREEN_KEY = ".scaffold_disclaimer_accepted"


def _check_smartscreen_disclaimer(root_dir: Path) -> bool:
    """Check if the SmartScreen disclaimer has been accepted (L1-35).

    On first run, Windows SmartScreen may flag the unsigned executable.
    This dialog informs the user and saves a flag so it's shown only once.

    Returns True if the user accepted (or already accepted previously).
    """
    flag_path = root_dir / _SMARTSCREEN_KEY
    if flag_path.exists():
        return True

    if not _HAS_TTK:
        return True

    result = Messagebox.okcancel(
        title="SCAFFOLD — First Run Notice",
        message=(
            "Windows SmartScreen may display a warning because this "
            "application is not signed with an Extended Validation (EV) "
            "code signing certificate.\n\n"
            "This is normal for new software. To proceed:\n"
            '1. Click "More info" on the SmartScreen dialog\n'
            '2. Click "Run anyway"\n\n'
            "SCAFFOLD runs entirely offline. No data is transmitted.\n\n"
            "Click OK to continue and suppress this message in the future."
        ),
    )
    if result == "OK":
        flag_path.write_text("accepted")
        return True
    return False


class ScaffoldApp:
    """Main GUI application for the SCAFFOLD Local Tool."""

    def __init__(self) -> None:
        if not _HAS_TTK:
            raise RuntimeError(
                "ttkbootstrap is required for the GUI. "
                "Install with: pip install ttkbootstrap==1.10.1"
            )

        self.root = ttk.Window(
            title="SCAFFOLD — Supply Chain Audit Tool",
            themename="darkly",
            size=(800, 700),
            resizable=(True, True),
        )
        self.root.minsize(700, 600)

        # State
        self._input_path = ttk.StringVar()
        self._pm_path = ttk.StringVar()
        self._bom_path = ttk.StringVar()
        self._sup_path = ttk.StringVar()
        self._password = ttk.StringVar()
        self._license_key = ttk.StringVar()
        self._output_dir = ttk.StringVar(value=str(Path.cwd() / "output"))
        self._export_kinaxis = ttk.BooleanVar(value=False)
        self._export_csv = ttk.BooleanVar(value=False)
        self._input_mode = ttk.StringVar(value="excel")
        self._running = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        # Main container with scrollable frame
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=BOTH, expand=True)

        # ── Title ─────────────────────────────────────────
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(
            title_frame,
            text="SCAFFOLD",
            font=("Helvetica", 20, "bold"),
            bootstyle="inverse-primary",
        ).pack(side=LEFT)
        ttk.Label(
            title_frame,
            text="  Supply Chain Structure Audit Tool",
            font=("Helvetica", 11),
            bootstyle="secondary",
        ).pack(side=LEFT, padx=(10, 0))

        # ── Input Mode ────────────────────────────────────
        input_frame = ttk.LabelFrame(main, text="Input Data", padding=10)
        input_frame.pack(fill=X, pady=5)

        mode_frame = ttk.Frame(input_frame)
        mode_frame.pack(fill=X, pady=(0, 5))
        ttk.Radiobutton(
            mode_frame,
            text="Excel Workbook (.xlsx)",
            variable=self._input_mode,
            value="excel",
            command=self._toggle_input_mode,
            bootstyle="info",
        ).pack(side=LEFT, padx=(0, 15))
        ttk.Radiobutton(
            mode_frame,
            text="Separate CSV Files",
            variable=self._input_mode,
            value="csv",
            command=self._toggle_input_mode,
            bootstyle="info",
        ).pack(side=LEFT)

        # Excel input
        self._excel_frame = ttk.Frame(input_frame)
        self._excel_frame.pack(fill=X)
        self._file_row(self._excel_frame, "Excel File:", self._input_path, "excel")

        # CSV inputs
        self._csv_frame = ttk.Frame(input_frame)
        self._file_row(self._csv_frame, "Part Master:", self._pm_path, "csv")
        self._file_row(self._csv_frame, "BOM Structure:", self._bom_path, "csv")
        self._file_row(self._csv_frame, "Supplier Map:", self._sup_path, "csv")

        # ── Settings ──────────────────────────────────────
        settings_frame = ttk.LabelFrame(main, text="Settings", padding=10)
        settings_frame.pack(fill=X, pady=5)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=X, pady=2)
        ttk.Label(row1, text="Password (key.scaf):", width=20).pack(side=LEFT)
        ttk.Entry(row1, textvariable=self._password, show="*").pack(
            side=LEFT, fill=X, expand=True, padx=(5, 0)
        )

        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=X, pady=2)
        ttk.Label(row2, text="License Key:", width=20).pack(side=LEFT)
        ttk.Entry(row2, textvariable=self._license_key).pack(
            side=LEFT, fill=X, expand=True, padx=(5, 0)
        )

        row3 = ttk.Frame(settings_frame)
        row3.pack(fill=X, pady=2)
        ttk.Label(row3, text="Output Directory:", width=20).pack(side=LEFT)
        ttk.Entry(row3, textvariable=self._output_dir).pack(
            side=LEFT, fill=X, expand=True, padx=(5, 0)
        )
        ttk.Button(
            row3, text="Browse", bootstyle="outline",
            command=self._browse_output_dir,
        ).pack(side=LEFT, padx=(5, 0))

        # ── Export Options ────────────────────────────────
        export_frame = ttk.LabelFrame(main, text="Export Plugins", padding=10)
        export_frame.pack(fill=X, pady=5)
        ttk.Checkbutton(
            export_frame,
            text="Kinaxis V7 RapidResponse CSV",
            variable=self._export_kinaxis,
            bootstyle="success-round-toggle",
        ).pack(side=LEFT, padx=(0, 20))
        ttk.Checkbutton(
            export_frame,
            text="Generic CSV Export",
            variable=self._export_csv,
            bootstyle="success-round-toggle",
        ).pack(side=LEFT)

        # ── Run Button ────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=10)
        self._run_btn = ttk.Button(
            btn_frame,
            text="Run SCAFFOLD Pipeline",
            bootstyle="success",
            command=self._on_run,
            width=30,
        )
        self._run_btn.pack()

        # ── Log Output ────────────────────────────────────
        log_frame = ttk.LabelFrame(main, text="Log", padding=5)
        log_frame.pack(fill=BOTH, expand=True, pady=5)
        self._log_text = ttk.Text(log_frame, height=12, state="disabled", wrap="word")
        self._log_text.pack(fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self._log_text, command=self._log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._log_text.configure(yscrollcommand=scrollbar.set)

    def _file_row(
        self, parent: ttk.Frame, label: str, var: ttk.StringVar, kind: str,
    ) -> None:
        """Add a file picker row."""
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=2)
        ttk.Label(row, text=label, width=15).pack(side=LEFT)
        ttk.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))

        filetypes = (
            [("Excel files", "*.xlsx *.xls")]
            if kind == "excel"
            else [("CSV files", "*.csv")]
        )

        def browse():
            from tkinter.filedialog import askopenfilename
            path = askopenfilename(filetypes=filetypes + [("All files", "*.*")])
            if path:
                var.set(path)

        ttk.Button(row, text="Browse", bootstyle="outline", command=browse).pack(
            side=LEFT, padx=(5, 0)
        )

    def _toggle_input_mode(self) -> None:
        """Switch between Excel and CSV input modes."""
        if self._input_mode.get() == "excel":
            self._csv_frame.pack_forget()
            self._excel_frame.pack(fill=X)
        else:
            self._excel_frame.pack_forget()
            self._csv_frame.pack(fill=X)

    def _browse_output_dir(self) -> None:
        from tkinter.filedialog import askdirectory
        path = askdirectory()
        if path:
            self._output_dir.set(path)

    def _log(self, msg: str) -> None:
        """Append a message to the log text widget (thread-safe)."""
        def _append():
            self._log_text.configure(state="normal")
            self._log_text.insert("end", msg + "\n")
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
        self.root.after(0, _append)

    def _on_run(self) -> None:
        """Start the pipeline in a background thread."""
        if self._running:
            return
        self._running = True
        self._run_btn.configure(state="disabled", text="Running...")
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self) -> None:
        """Execute the SCAFFOLD pipeline (runs in background thread)."""
        try:
            self._log("=== SCAFFOLD Pipeline Starting ===")
            self._log("")

            import pandas as pd
            import orjson

            from local.core.graph import build_digraph, detect_cycles, detect_orphans
            from local.core.validation import (
                validate_bom,
                validate_end_products_have_bom,
                validate_part_master,
                validate_supplier_map,
                validate_usage_share,
            )
            from local.core.reader import normalize_input_dtypes
            from local.core.output import (
                generate_key_data,
                generate_key_scaf,
                generate_upload_json,
            )
            from local.core.licensing import (
                verify_license,
                check_free_tier_limits,
                TIER_FREE,
                TIER_HEAVY,
            )
            from local.reports.reports import (
                generate_network_summary,
                timestamped_filename,
                validate_and_annotate,
                generate_audit_report_data,
                render_audit_report_pdf,
            )

            out_dir = Path(self._output_dir.get())
            out_dir.mkdir(parents=True, exist_ok=True)

            # License check
            tier = TIER_FREE
            license_key = self._license_key.get().strip()
            if license_key:
                result = verify_license(license_key)
                if result:
                    tier = result
                    self._log(f"License verified: {tier} tier")
                else:
                    self._log("WARNING: Invalid license key — Free tier")

            # Read inputs
            self._log("[1/6] Reading input files...")
            if self._input_mode.get() == "excel":
                input_path = Path(self._input_path.get())
                from local.core.reader import read_part_master, read_bom, read_supplier_map
                pm_df = read_part_master(input_path)
                bom_df = read_bom(input_path)
                sup_df = read_supplier_map(input_path)
            else:
                pm_df = pd.read_csv(self._pm_path.get())
                bom_df = pd.read_csv(self._bom_path.get())
                sup_df = pd.read_csv(self._sup_path.get())

            pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
                lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
            )
            # Coerce identity columns to string so node tuples match across tabs
            pm_df, bom_df, sup_df = normalize_input_dtypes(pm_df, bom_df, sup_df)
            self._log(
                f"      Part Master: {len(pm_df)} | "
                f"BOM: {len(bom_df)} | "
                f"Suppliers: {len(sup_df)}"
            )

            # Validate
            self._log("[2/6] Validating schema...")
            errors = []
            errors.extend(validate_part_master(pm_df))
            errors.extend(validate_bom(bom_df))
            errors.extend(validate_supplier_map(sup_df))
            errors.extend(validate_usage_share(bom_df))
            errors.extend(validate_end_products_have_bom(pm_df, bom_df))
            if errors:
                for e in errors:
                    self._log(f"  ERROR: {e}")
                self._log("Pipeline stopped due to validation errors.")
                return
            self._log("      PASSED")

            # Build graph
            self._log("[3/6] Building BOM graph...")
            G = build_digraph(bom_df)
            self._log(f"      {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

            cycles = detect_cycles(G)
            if cycles:
                self._log(f"      WARNING: {len(cycles)} circular refs!")

            pm_nodes = {
                (row["PartNumber"], row["Site"]) for _, row in pm_df.iterrows()
            }
            end_products = set()
            for _, row in pm_df[pm_df["IsEndProduct"]].iterrows():
                end_products.add((row["PartNumber"], row["Site"]))
            self._log(f"      {len(end_products)} end products")

            # Summary + reports
            self._log("[4/6] Computing risk metrics & reports...")
            summary = generate_network_summary(G, pm_df, end_products, sup_df)

            # Validated Excel
            validation_results = validate_and_annotate(pm_df, bom_df, sup_df)

            # PDF report
            report_data = generate_audit_report_data(summary, validation_results)
            pdf_path = out_dir / timestamped_filename("report", "pdf")
            render_audit_report_pdf(report_data, pdf_path)
            self._log(f"      Written: {pdf_path.name}")

            # Tier gate
            if tier == TIER_FREE:
                limit_err = check_free_tier_limits(pm_df, bom_df)
                if limit_err:
                    self._log(f"      FREE TIER: {limit_err}")
                    self._log("      (validated.xlsx + report.pdf only)")
                    self._log("")
                    self._log("=== Pipeline complete (Free tier) ===")
                    return

            # upload.json
            if tier != TIER_FREE:
                self._log("[5/6] Generating upload.json...")
                upload_data = generate_upload_json(G, pm_df, sup_df, end_products)
                if license_key and tier != TIER_FREE:
                    from local.core.licensing import extract_tier_sig
                    tier_sig = extract_tier_sig(license_key)
                    if tier_sig:
                        upload_data["meta"]["tier"] = tier
                        upload_data["meta"]["tier_sig"] = tier_sig
                upload_path = out_dir / "upload.json"
                upload_path.write_bytes(
                    orjson.dumps(upload_data, option=orjson.OPT_INDENT_2)
                )
                self._log(f"      Written: upload.json ({upload_path.stat().st_size:,} bytes)")
            else:
                self._log("[5/6] Skipping upload.json (Free tier)")

            # key.scaf
            password = self._password.get().strip()
            if tier == TIER_HEAVY and password:
                self._log("[6/6] Generating key.scaf...")
                key_data = generate_key_data(G, pm_df, sup_df)
                key_bytes = generate_key_scaf(key_data, password=password)
                key_path = out_dir / "key.scaf"
                key_path.write_bytes(key_bytes)
                self._log(f"      Written: key.scaf ({key_path.stat().st_size:,} bytes)")
            else:
                self._log("[6/6] Skipping key.scaf")

            # Export plugins
            if self._export_kinaxis.get():
                self._log("Exporting Kinaxis V7 CSV...")
                from local.export.kinaxis_v7 import export_kinaxis_v7
                k_path = out_dir / timestamped_filename("kinaxis_v7", "csv")
                export_kinaxis_v7(G, pm_df, sup_df, bom_df, k_path)
                self._log(f"      Written: {k_path.name}")

            if self._export_csv.get():
                self._log("Exporting generic CSV...")
                from local.export.csv_export import export_generic_csv
                c_path = out_dir / timestamped_filename("export", "csv")
                export_generic_csv(G, pm_df, sup_df, bom_df, c_path)
                self._log(f"      Written: {c_path.name}")

            self._log("")
            self._log(f"=== Pipeline complete ({tier} tier) ===")
            self._log(f"    Output: {out_dir}/")

        except Exception as exc:
            self._log(f"\nERROR: {exc}")
            self._log(traceback.format_exc())
        finally:
            self._running = False
            self.root.after(0, lambda: self._run_btn.configure(
                state="normal", text="Run SCAFFOLD Pipeline"
            ))

    def run(self) -> None:
        """Start the GUI event loop."""
        # L1-35: SmartScreen disclaimer on first run
        app_dir = Path.home() / ".scaffold"
        app_dir.mkdir(exist_ok=True)
        if not _check_smartscreen_disclaimer(app_dir):
            self.root.destroy()
            return
        self.root.mainloop()


def launch_gui() -> None:
    """Entry point for the SCAFFOLD desktop GUI."""
    app = ScaffoldApp()
    app.run()


if __name__ == "__main__":
    launch_gui()
