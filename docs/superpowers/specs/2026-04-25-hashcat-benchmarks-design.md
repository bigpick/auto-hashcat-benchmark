# Hashcat GPU Benchmark Hub — Design Spec

## Overview

A GitHub repository and GitHub Pages site that provides centralized, standardized hashcat GPU speed benchmarks. Automated infrastructure rents GPU instances on Vast.ai, runs hashcat benchmarks in a controlled container environment, and publishes results to an interactive single-page dashboard.

## Goals

1. Standardized, reproducible benchmarks across a wide matrix of GPU models
2. Interactive web dashboard for filtering, comparing, and exporting results
3. Automated infrastructure to rent GPUs, run benchmarks, and collect results
4. Idempotent orchestration — never re-run a benchmark that already exists
5. Cost-aware tooling with estimation before execution

## Non-Goals (for now)

- Community-submitted benchmark results (users can request GPU models via issues)
- Multi-GPU benchmarks (single GPU only)
- Continuous/scheduled runs (manual one-off execution only)
- GitHub Actions-based benchmark orchestration (CI only builds/publishes the site)

---

## Architecture

### Local Orchestrator Model

All benchmark execution is driven from the operator's local machine. The Python CLI calls Vast.ai to rent GPU instances, SSHes into them to run the benchmark container, pulls results back, and writes them to the repo. GitHub Actions is only responsible for building the site index and deploying to GitHub Pages on push to main.

```
Local machine:
  Justfile → Python CLI → Vast.ai API → Rent GPU instance
                        → SSH → docker run hashcat-bench
                        → Pull results JSON
                        → Write to data/results/
                        → git push

GitHub:
  on push to main → build index.json → vite build → deploy to Pages
```

---

## Repository Layout

```
hashcat-benchmarks/
├── Justfile                          # Command interface for all operations
├── pyproject.toml                    # Python project managed by uv
├── src/
│   └── hashcat_bench/
│       ├── __init__.py
│       ├── cli.py                    # CLI entrypoint
│       ├── provider.py               # Vast.ai integration (search, rent, destroy)
│       ├── runner.py                 # SSH into instance, run container, collect output
│       ├── parser.py                 # Parse hashcat machine-readable output → JSON
│       ├── data.py                   # Manage result files, check idempotency, build index
│       └── estimator.py             # Cost estimation from Vast.ai pricing
├── container/
│   ├── Dockerfile                    # hashcat benchmark image
│   └── entrypoint.sh                # Run benchmark, collect GPU info, output JSON
├── data/
│   ├── results/                      # One JSON file per (hashcat_version, gpu_model)
│   │   ├── v6.2.6/
│   │   │   ├── rtx-4090.json
│   │   │   └── rtx-3080.json
│   │   └── v6.2.5/
│   │       └── rtx-4090.json
│   ├── index.json                    # Consolidated index, built during site build
│   └── gpu-models.json               # Canonical list of GPU models in the matrix
├── site/                             # Svelte + Vite frontend
│   ├── src/
│   │   ├── App.svelte
│   │   ├── main.js
│   │   └── lib/
│   │       ├── FilterBar.svelte      # Version, GPU, hash mode filters
│   │       ├── TableView.svelte      # Dense sortable data table
│   │       ├── CompareView.svelte    # GPU card selection + bar charts
│   │       └── ExportButton.svelte   # CSV/JSON export
│   ├── package.json
│   └── vite.config.js
├── .github/
│   └── workflows/
│       └── deploy.yml                # Build index + Svelte site, deploy to Pages
└── .gitignore
```

---

## Data Schema

### Unique Key

`(hashcat_version, gpu_model, kernel_mode)` — if a result file exists for this tuple, the orchestrator skips the run.

### Result File Path

`data/results/{hashcat_version}/{gpu_model_slug}.json` for optimized mode (default).
`data/results/{hashcat_version}/{gpu_model_slug}-default.json` for non-optimized mode.

Optimized mode (`-O`) is the standard run. Non-optimized runs are opt-in and use a `-default` suffix to avoid file collisions.

### Result File Schema

```json
{
  "hashcat_version": "v6.2.6",
  "gpu_model": "RTX 4090",
  "container_image": "ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
  "driver_version": "535.129.03",
  "cuda_version": "12.2",
  "kernel_mode": "optimized",
  "benchmark_date": "2026-04-25T14:30:00Z",
  "benchmarks": [
    {
      "hash_mode": 0,
      "hash_name": "MD5",
      "speed": 164000000000,
      "exec_runtime_ms": 12.5
    },
    {
      "hash_mode": 100,
      "hash_name": "SHA1",
      "speed": 56000000000,
      "exec_runtime_ms": 18.2
    }
  ]
}
```

- `speed` is in hashes/second (integer)
- `gpu_model_slug` is a URL-safe lowercase version of the GPU name (e.g., `rtx-4090`)
- `driver_version` is captured from the host at runtime (not pinned — it varies by Vast.ai instance)
- `kernel_mode` is either `"optimized"` or `"default"`, controlled by whether `-O` is passed

### Index File: `data/index.json`

Built by a Python script during the site build. Consolidates all result files into a single JSON for the frontend to fetch.

```json
{
  "generated_at": "2026-04-25T15:00:00Z",
  "versions": ["v6.2.6", "v6.2.5"],
  "gpu_models": ["RTX 4090", "RTX 3080", "RTX 3060"],
  "hash_modes": [
    {"mode": 0, "name": "MD5"},
    {"mode": 100, "name": "SHA1"}
  ],
  "results": [
    {
      "hashcat_version": "v6.2.6",
      "gpu_model": "RTX 4090",
      "driver_version": "535.129.03",
      "cuda_version": "12.2",
      "kernel_mode": "optimized",
      "benchmark_date": "2026-04-25T14:30:00Z",
      "benchmarks": [
        {"hash_mode": 0, "speed": 164000000000, "exec_runtime_ms": 12.5},
        {"hash_mode": 100, "speed": 56000000000, "exec_runtime_ms": 18.2}
      ]
    }
  ]
}
```

### GPU Models File: `data/gpu-models.json`

Canonical list of GPU models in the benchmark matrix. Edited manually when adding new models.

```json
{
  "models": [
    {"name": "RTX 4090", "slug": "rtx-4090", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4090"},
    {"name": "RTX 4080", "slug": "rtx-4080", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4080"},
    {"name": "RTX 3090", "slug": "rtx-3090", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3090"},
    {"name": "RTX 3080", "slug": "rtx-3080", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3080"},
    {"name": "RTX 3060", "slug": "rtx-3060", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3060"}
  ]
}
```

---

## Justfile Command Interface

```just
# Discovery
list-gpus:              # Query Vast.ai for available GPU models + current $/hr
list-gpus-filtered FILTER: # Filter by name substring (e.g., "RTX 40")

# Cost Estimation (no money spent)
estimate GPU HASHCAT:   # Estimate cost for a single GPU benchmark
estimate-matrix HASHCAT: # Estimate cost for full GPU matrix, show skips

# Container Management
build-image HASHCAT:    # Build Docker image for a hashcat version
push-image HASHCAT:     # Push image to GHCR

# Benchmark Execution
bench GPU HASHCAT:      # Run single GPU benchmark
bench-matrix HASHCAT:   # Run full GPU matrix (sequential)
bench-matrix-parallel HASHCAT N="3": # Run matrix with N concurrent instances
bench-matrix-capped HASHCAT BUDGET: # Run matrix, abort if estimate > $BUDGET

# Data Management
build-index:            # Regenerate data/index.json from data/results/
validate:               # Validate all result JSON files against schema

# Frontend
dev:                    # Start Vite dev server for local preview
build-site:             # Build production site

# Utilities
status:                 # Show what results exist, what's missing per version
```

---

## Container Design

### Dockerfile

Based on `nvidia/cuda:12.2.0-devel-ubuntu22.04`. Accepts `HASHCAT_VERSION` as a build arg. Compiles hashcat from source at the pinned git tag. The NVIDIA driver is host-provided (standard for GPU containers via `--gpus all`).

### Entrypoint Script

1. Runs `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader` to capture GPU metadata
2. Runs `hashcat -b --machine-readable` (with optional `-O` for optimized kernels)
3. Parses both outputs into the result JSON schema
4. Writes JSON to stdout

The entrypoint is self-contained — no Python dependencies in the container. It's a bash script that produces JSON. The Python tooling on the local machine handles everything else.

### Controlled vs. Uncontrolled Variables

| Variable | Controlled? | Source |
|----------|-------------|--------|
| Hashcat version | Yes | Container build arg |
| CUDA toolkit version | Yes | Base image tag |
| OS | Yes | Base image |
| Kernel mode (-O) | Yes | Entrypoint flag |
| GPU model | Selected | Vast.ai search filter |
| NVIDIA driver version | No | Host-provided, captured in results |

---

## Frontend: Svelte + Vite Dashboard

### Single-Page Application

One page, two tabbed views, shared filter bar.

### Filter Bar (shared across both views)

- **Hashcat version dropdown** — populated from `index.json` versions list
- **GPU model multi-select** — populated from `index.json` gpu_models list, with family grouping
- **Hash mode search** — text search across mode number and name
- **Export button** — download filtered data as CSV or JSON

### Table View (default tab)

Dense sortable data table. Columns: hash mode number, hash type name, one speed column per selected GPU. Click column headers to sort. Speeds displayed in human-readable format (GH/s, MH/s, kH/s) with the raw number available on hover. 300+ rows for a full hash mode sweep.

### Compare View

GPU selection cards at top (click to toggle). Below, horizontal bar chart comparing selected GPUs for a chosen hash mode. Shows relative performance (e.g., "RTX 4090 is 2.0x faster than RTX 3080"). Useful for quick "which GPU is fastest for X" questions.

### Deployment

GitHub Actions workflow on push to main:
1. Run Python script to build `data/index.json` from `data/results/**/*.json`
2. Copy `data/index.json` into `site/public/`
3. Run `npm run build` (Vite)
4. Deploy `site/dist/` to GitHub Pages

---

## Vast.ai Integration

### Instance Lifecycle

1. **Search**: `vastai search offers 'gpu_name=RTX_4090 num_gpus=1'` — find cheapest single-GPU instance
2. **Rent**: Create instance with the benchmark Docker image
3. **Wait**: Poll instance status until benchmark completes
4. **Collect**: Pull JSON output from the instance
5. **Destroy**: Delete instance immediately to stop billing

### GPU Name Mapping

Vast.ai uses its own GPU naming conventions. The `gpu-models.json` file includes a mapping field to translate between our canonical names and Vast.ai search terms. The `list-gpus` command queries Vast.ai and shows which of our target models are currently available and at what price.

### Cost Estimation

The estimator queries Vast.ai for the current cheapest offer per GPU model and multiplies by an estimated runtime. Runtime estimates are stored per GPU family (based on historical data — faster GPUs complete the benchmark sweep faster). The estimate includes a safety margin (e.g., 1.5x estimated runtime).

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Command interface | Justfile (just) |
| Benchmark tooling | Python 3.12+, managed by uv |
| Cloud provider | Vast.ai (SDK/CLI) |
| Container | Docker, nvidia/cuda base image |
| Frontend | Svelte + Vite |
| Charts | Chart.js |
| CI/CD | GitHub Actions |
| Hosting | GitHub Pages |
| Container registry | GitHub Container Registry (ghcr.io) |

---

## Initial GPU Target Matrix

Starting with mainstream NVIDIA consumer GPUs:

**RTX 50 series**: RTX 5090, RTX 5080, RTX 5070 Ti, RTX 5070
**RTX 40 series**: RTX 4090, RTX 4080, RTX 4070 Ti, RTX 4070, RTX 4060 Ti, RTX 4060
**RTX 30 series**: RTX 3090, RTX 3080, RTX 3070, RTX 3060

RTX 10/20 series and AMD GPUs are deferred based on Vast.ai availability and cost. Datacenter GPUs (A100, H100, L4) are also deferred.

---

## Cost Estimate

Rough estimate for a full matrix run (14 GPUs, one hashcat version):

- Average Vast.ai spot price for consumer GPUs: ~$0.15-0.50/hr
- Estimated benchmark runtime per GPU: ~10-20 minutes
- Estimated cost per GPU: ~$0.03-0.17
- **Estimated total for 14 GPUs: ~$0.50-2.50 per hashcat version**

This is a rough estimate. The `estimate-matrix` command provides accurate pricing from live Vast.ai data before any money is spent.
