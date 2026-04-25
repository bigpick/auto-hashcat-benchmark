# Development Guide

## Prerequisites

- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js 22+](https://nodejs.org/) (for the frontend)
- [Just](https://github.com/casey/just) (command runner)
- [Docker](https://docs.docker.com/) (for building benchmark containers)

For running benchmarks, you also need a [Vast.ai](https://vast.ai) account and API key.

## Setup

```bash
just setup
```

This installs Python dependencies (via uv), Node dependencies (via npm) for the frontend, and installs [pre-commit](https://pre-commit.com/) hooks for secret scanning and code hygiene.

### Secret Scanning

A `pre-commit` hook using [ripsecrets](https://github.com/sirwart/ripsecrets) runs automatically on every commit to prevent accidental credential leaks. Additional hooks check for private keys, merge conflicts, and large files.

To run the hooks manually against all files:

```bash
just lint --all-files
```

## Project Structure

```
hashcat-benchmarks/
├── src/hashcat_bench/       # Python CLI and orchestration
│   ├── cli.py               # CLI entrypoint (argparse)
│   ├── models.py            # Dataclasses: BenchmarkResult, GpuModel, etc.
│   ├── parser.py            # Parse hashcat --machine-readable output
│   ├── data.py              # Result file I/O, idempotency, index builder
│   ├── provider.py          # Vast.ai SDK wrapper
│   ├── estimator.py         # Cost estimation
│   └── runner.py            # SSH into instances, run benchmarks, collect results
├── container/
│   ├── Dockerfile           # Builds hashcat at a pinned version
│   └── entrypoint.sh        # Runs benchmark, outputs JSON
├── data/
│   ├── gpu-models.json      # Canonical GPU model list (edit to add GPUs)
│   ├── results/             # One JSON file per (version, gpu_model)
│   └── index.json           # Built from results/ during site build
├── site/                    # Svelte 5 + Vite frontend
│   ├── src/
│   │   ├── App.svelte       # Main app with filter bar, tabs, views
│   │   └── lib/             # FilterBar, TableView, CompareView, ExportButton
│   └── public/
│       └── index.json       # Copied from data/ during build
├── tests/                   # pytest test suite
├── Justfile                 # All commands
└── pyproject.toml           # Python project config
```

## Running Tests

```bash
just test              # run all tests
just test -v           # verbose
just test -k parser    # run only parser tests
just test-cov          # with coverage report
```

## Frontend Development

```bash
just dev               # starts Vite dev server at http://localhost:5173
```

The dev server uses `site/public/index.json` as sample data. Edit that file to test with different data shapes.

To build the production site:

```bash
just build-site        # builds index.json from data/results/, then builds the Svelte app
```

Output goes to `site/dist/`.

## Benchmark Workflow

### 1. Build the container image

```bash
just build-image v6.2.6
just push-image v6.2.6
```

This compiles hashcat at the pinned version inside a `nvidia/cuda:12.2.0` container and pushes it to GHCR. Only needed once per hashcat version.

### 2. Configure Vast.ai

Set your API key:

```bash
export VAST_API_KEY=your_key_here
```

Or add it to a `.env` file in the project root (the Justfile loads `.env` automatically).

### 3. Explore available GPUs

```bash
just list-gpus                  # all target GPUs
just list-gpus "RTX 40"         # filter to RTX 40 series
```

Shows availability count and cheapest $/hr for each GPU model on Vast.ai.

### 4. Estimate costs

```bash
just estimate rtx-4090 v6.2.6          # single GPU
just estimate-matrix v6.2.6            # full matrix with skip detection
```

The estimator queries live Vast.ai pricing and applies a 1.5x safety margin to the runtime estimate. It also checks which results already exist and marks them as "skip".

### 5. Run benchmarks

```bash
just bench rtx-4090 v6.2.6                    # single GPU
just bench-matrix v6.2.6                       # full matrix (sequential)
just bench-matrix-capped v6.2.6 5.00           # abort if estimate > $5
```

The orchestrator:
1. Checks if results already exist (skips if so)
2. Finds the cheapest Vast.ai instance for the target GPU
3. Rents it, waits for SSH readiness
4. Runs the benchmark container
5. Collects the JSON result
6. Destroys the instance
7. Saves the result to `data/results/{version}/{gpu-slug}.json`

### 6. Check status

```bash
just status v6.2.6             # shows OK/MISSING for each GPU in the matrix
```

### 7. Publish

After collecting results, commit the new files in `data/results/` and push. GitHub Actions will rebuild the index and deploy the site.

## Adding a New GPU Model

Edit `data/gpu-models.json` and add an entry:

```json
{"name": "RTX 4080 SUPER", "slug": "rtx-4080-super", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4080 SUPER"}
```

- `slug` - URL-safe lowercase identifier (used in file paths and CLI arguments)
- `vastai_name` - the name Vast.ai uses in its search API

Run `just list-gpus` to verify Vast.ai has instances available for the new model.

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `VAST_API_KEY` | Vast.ai API authentication | For benchmarking |
| `HASHCAT_BENCH_REGISTRY` | Container registry (default: `ghcr.io/YOUR_USERNAME/hashcat-bench`) | For container push |

## Data Schema

Each result file (`data/results/{version}/{gpu-slug}.json`):

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
    {"hash_mode": 0, "hash_name": "MD5", "speed": 164000000000, "exec_runtime_ms": 12.5}
  ]
}
```

The unique key is `(hashcat_version, gpu_model, kernel_mode)`. Optimized mode (`-O`) is the default; non-optimized results use a `-default` filename suffix.

## Controlled Variables

| Variable | Pinned? | Source |
|----------|---------|--------|
| Hashcat version | Yes | Container build arg |
| CUDA toolkit | Yes | Base image tag (12.2) |
| OS | Yes | Ubuntu 22.04 |
| Kernel mode | Yes | Entrypoint flag |
| GPU model | Selected | Vast.ai search filter |
| NVIDIA driver | No | Host-provided, captured in results |
