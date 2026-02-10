# SCAFFOLD Local Tool — Offline Usage Guide

Portable, offline-first BOM audit tool. Works on any machine with Python 3.11+ — no internet required after initial setup.

## Quick Start (2 minutes)

```bash
# 1. Install dependencies (one-time, needs internet)
pip install -r requirements.txt

# 2. Run with your data
python -m local.cli \
  --pm   your_part_master.csv \
  --bom  your_bom_structure.csv \
  --sup  your_supplier_map.csv \
  --password YOUR_PASSWORD \
  --output-dir output/
```

Output:
- `output/upload.json` — masked data for SaaS viewer
- `output/key.scaf` — encrypted restore key (stays with you)
- `output/summary_*.txt` — network statistics

## Try the Demo

```bash
# Generate semiconductor demo (Fab → CP → Bumping → Assembly → FT)
python demo/generate_demo.py

# Files created:
#   demo/upload.json   — drop into SaaS viewer
#   demo/key.scaf      — drop to unmask (password: scaffold-demo)
```

## Constrained Internet Setup

For air-gapped or restricted-network environments:

### Option A: Pre-download wheels (recommended)

On a machine WITH internet:

```bash
# Download all dependencies as wheel files
pip download -r requirements.txt -d ./wheels/
```

Copy the `wheels/` folder and the SCAFFOLD project to the target machine via USB/secure transfer.

On the target machine (NO internet):

```bash
# Install from local wheels
pip install --no-index --find-links ./wheels/ -r requirements.txt

# Verify installation
python -c "import pandas, networkx, orjson, cryptography; print('OK')"

# Run
python -m local.cli --pm data/pm.csv --bom data/bom.csv --sup data/sup.csv \
  --password SECRET --output-dir output/
```

### Option B: Portable Python (Windows)

1. Download [Python Embeddable](https://www.python.org/downloads/) (zip, ~25MB)
2. Extract to a USB drive
3. Copy SCAFFOLD project + pre-downloaded wheels
4. Run:

```cmd
python\python.exe -m pip install --no-index --find-links wheels\ -r requirements.txt
python\python.exe -m local.cli --pm data\pm.csv --bom data\bom.csv --sup data\sup.csv --password SECRET
```

### Option C: Docker (if available)

```bash
# Build once (needs internet)
docker build -t scaffold .

# Run offline forever
docker run --rm -v $(pwd)/data:/data scaffold \
  python -m local.cli --pm /data/pm.csv --bom /data/bom.csv --sup /data/sup.csv \
  --password SECRET --output-dir /data/output/
```

## Input Data Format

Prepare three CSV files:

### 1. Part Master (`--pm`)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| PartNumber | string | Yes | Part identifier |
| Site | string | Yes | Manufacturing/warehouse site |
| Stage | string | Yes | Process stage (e.g., Fabrication, Assembly) |
| IsEndProduct | boolean | Yes | TRUE for finished goods |

### 2. BOM Structure (`--bom`)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| AssemblyName | string | Yes | Parent part |
| AssemblySite | string | Yes | Parent site |
| ComponentName | string | Yes | Child part |
| ComponentSite | string | Yes | Child site |
| Qty | number | Yes | Quantity per |
| SubGroup | string | No | Alternate group ID |
| UsageShare | number | No | Share within SubGroup (must sum to 1.0) |

### 3. Supplier Map (`--sup`)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| Part | string | Yes | Part identifier |
| Supplier | string | Yes | Supplier name |
| LeadTime | number | Yes | Lead time in days |

## CLI Options

```
python -m local.cli [options]

Required:
  --pm FILE          Part Master CSV
  --bom FILE         BOM Structure CSV
  --sup FILE         Supplier Map CSV

Optional:
  --password TEXT     Password for key.scaf (omit to skip key generation)
  --output-dir DIR   Output directory (default: output/)
  --skip-key         Skip key.scaf generation (Light tier)
  --validate-only    Only validate inputs, no output files
```

## Pipeline Steps

```
[1/6] Read CSV inputs
[2/6] Validate schema (columns, types, SubGroup shares)
[3/6] Build BOM graph (NetworkX DiGraph)
      - Detect circular references
      - Detect orphan parts
[4/6] Compute risk metrics
      - Max lead time per part
      - Single-source detection
      - Network summary statistics
[5/6] Generate upload.json (masked)
      - SHA-256 hash all names
      - Mask stages (S1, S2, S3...)
      - Jitter numeric values (±15%)
      - Compute paths via DFS
[6/6] Generate key.scaf (encrypted)
      - PBKDF2 key derivation (1.2M iterations)
      - Fernet encryption (AES-128-CBC)
      - zlib compression
```

## Security Notes

- **Zero network calls**: The local tool makes no outbound connections. Ever.
- **key.scaf never uploaded**: Contains the real-name mapping, password-protected.
- **upload.json is safe to share**: All values are hashed, masked, or jittered.
- **Verify offline**: `python -c "import socket; socket.setdefaulttimeout(0.001)"` before running to confirm no network dependency.
