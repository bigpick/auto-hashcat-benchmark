# Hashcat GPU Benchmarks

Centralized, standardized [hashcat](https://github.com/hashcat/hashcat) GPU speed benchmarks with automated infrastructure and an interactive web dashboard.

**Live site:** *Coming soon — deploy via GitHub Pages*

## Why This Exists

Hashcat benchmark results are scattered across GitHub gists, forum posts, and random wikis. Each uses different hashcat versions, driver versions, and configurations, making meaningful GPU comparisons nearly impossible.

This project fixes that by:

- Running every benchmark in an **identical containerized environment** — same hashcat build, same CUDA toolkit, same OS — so the only variable is the GPU
- Covering a **wide matrix of GPU models** across NVIDIA's RTX 30, 40, and 50 series
- Publishing results to an **interactive dashboard** where you can filter by hashcat version, select GPUs, sort by hash mode, and compare speeds side-by-side
- Providing **cost-aware tooling** that estimates Vast.ai rental costs before spending anything

## Dashboard Features

- **Table View** — dense sortable table with all hash modes and selected GPUs as columns. Speeds formatted as GH/s, MH/s, etc. with raw values on hover.
- **Compare View** — select a hash mode, see a bar chart comparing GPU speeds with relative performance ratios (e.g., "RTX 4090 is 2.0x faster than RTX 3080").
- **Filters** — filter by hashcat version, toggle GPU models on/off, search hash modes by name or number.
- **Export** — download filtered results as CSV or JSON.

## GPU Coverage

Currently targeting mainstream NVIDIA consumer GPUs:

| Series | Models |
|--------|--------|
| RTX 50 (Blackwell) | 5090, 5080, 5070 Ti, 5070 |
| RTX 40 (Ada Lovelace) | 4090, 4080, 4070 Ti, 4070, 4060 Ti, 4060 |
| RTX 30 (Ampere) | 3090, 3080, 3070, 3060 |

RTX 10/20 series, AMD GPUs, and datacenter GPUs (A100, H100) may be added based on availability and cost.

## How It Works

1. A **Docker container** compiles hashcat at a pinned version on `nvidia/cuda:12.2.0-devel-ubuntu22.04`
2. A **Python CLI** rents GPU instances on [Vast.ai](https://vast.ai), runs the container, and collects structured JSON results
3. Results are stored in the repo as one JSON file per `(hashcat_version, gpu_model)` pair
4. **GitHub Actions** builds a consolidated index and deploys the Svelte dashboard to GitHub Pages

The orchestrator is **idempotent** — it skips any benchmark that already has results for the given hashcat version + GPU + kernel mode combination.

## Quick Start

```bash
# Install dependencies
just setup

# See what GPUs are available on Vast.ai right now
just list-gpus

# Estimate cost for a full benchmark run
just estimate-matrix v6.2.6

# Run a single benchmark
just bench rtx-4090 v6.2.6

# Run the full matrix (sequential)
just bench-matrix v6.2.6

# Preview the dashboard locally
just dev
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full setup and development instructions.

## Requesting New GPU Models

Open an issue with the GPU model name. If it's available on Vast.ai at a reasonable cost, we'll add it to the matrix.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| CLI / Orchestration | Python 3.12+, [uv](https://docs.astral.sh/uv/) |
| Cloud GPU Rental | [Vast.ai](https://vast.ai) SDK |
| Benchmark Container | Docker, nvidia/cuda base |
| Frontend | Svelte 5, Vite, Chart.js |
| Command Interface | [Just](https://github.com/casey/just) |
| CI/CD | GitHub Actions |
| Hosting | GitHub Pages |

## License

TBD
