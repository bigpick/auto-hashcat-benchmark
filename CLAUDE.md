# CLAUDE.md

Project-specific instructions for Claude Code when working in this repository.

## Project Overview

Hashcat GPU benchmark hub: automated infrastructure for renting GPU instances on Vast.ai, running standardized hashcat benchmarks in Docker containers, and publishing results to a GitHub Pages dashboard.

## Architecture

- **Python CLI** (`src/hashcat_bench/`) — orchestrates Vast.ai GPU rentals, runs benchmarks, manages result data. Managed by `uv`.
- **Docker container** (`container/`) — compiles hashcat from source at a pinned version, runs `hashcat -b --machine-readable`, outputs structured JSON.
- **Svelte frontend** (`site/`) — single-page dashboard with filter bar, sortable table view, Chart.js comparison view, and CSV/JSON export. Built with Vite.
- **GitHub Actions** (`.github/workflows/deploy.yml`) — builds the data index and deploys the Svelte site to GitHub Pages on push to main.
- **Justfile** — command interface for everything.

## Key Commands

```bash
just setup              # install all dependencies (Python + Node)
just test               # run pytest suite
just test -v            # verbose tests
just dev                # start frontend dev server
just build-site         # build production site
just build-index        # regenerate data/index.json from results
just list-gpus          # query Vast.ai for GPU availability
just status v6.2.6      # check which GPUs have results
```

## Code Conventions

### Python (`src/hashcat_bench/`)

- Python 3.12+, managed by `uv`
- Standard library dataclasses for models (no Pydantic)
- Imports from external services (vastai, paramiko) are deferred inside functions to keep module loading fast and test-friendly
- Tests use `pytest` with `tmp_path` fixtures; external APIs are mocked with `unittest.mock`
- Provider/runner/estimator accept injected dependencies for testability

### Frontend (`site/`)

- Svelte 5 with runes syntax: `$state()`, `$derived()`, `$effect()`, `$props()`, `$bindable()`
- Do NOT use Svelte 4 syntax (`export let`, `$:` reactive declarations, `on:click`)
- Chart.js with tree-shaken imports (register only needed components)
- Dark theme (`#0f172a` background)

### Data

- Results stored at `data/results/{hashcat_version}/{gpu-slug}.json`
- Unique key: `(hashcat_version, gpu_model, kernel_mode)`
- Optimized mode (`-O`) is default; non-optimized uses `-default` filename suffix
- `data/index.json` is generated (gitignored), not hand-edited
- `data/gpu-models.json` is the canonical GPU list, edited manually

### Justfile

- All user-facing commands go through the Justfile
- Python commands use `uv run` (via the `python` variable)
- Frontend commands `cd` into `site/` first

## Testing

- Run `just test` before any PR
- All Python modules have corresponding `tests/test_{module}.py`
- Tests must not make real network calls (mock Vast.ai SDK, paramiko)
- Use `tmp_path` for any file I/O in tests

## Secrets and Credentials

- **Never hardcode** API keys, tokens, or passwords in source files
- Secrets are provided exclusively via environment variables (`VAST_API_KEY`, etc.)
- `.env` files are gitignored; `.env.example` documents required variables without values
- `pre-commit` hooks with `ripsecrets` scan for accidental secret commits
- `VastProvider` requires `VAST_API_KEY` at runtime and raises a clear error if missing
- The `VastProvider.__repr__` is overridden to prevent accidental key leakage in logs/tracebacks
- When adding new integrations, follow the same pattern: env var, fail-fast if missing, no defaults that could mask a missing key
- Prefer established secret scanning tools (pre-commit, ripsecrets) over custom scripts

## Git Workflow

- The repository owner handles all git operations (commit, push, branch management)
- Do not run `git commit`, `git push`, `git init`, or any git write commands
- Do not amend, rebase, or force-push

## Common Tasks

**Adding a new hash mode name mapping:** Edit `HASH_MODE_NAMES` dict in `src/hashcat_bench/parser.py`.

**Adding a new GPU to the matrix:** Edit `data/gpu-models.json`. Use `just list-gpus` to verify Vast.ai availability.

**Changing the CUDA version:** Update the base image tag in `container/Dockerfile` and the `cuda_version` references in `runner.py` and `cli.py`.

**Updating the container registry:** Set `HASHCAT_BENCH_REGISTRY` env var or edit the default in the Justfile.

## File Map

| Path | Purpose |
|------|---------|
| `src/hashcat_bench/models.py` | BenchmarkEntry, BenchmarkResult, GpuModel, GpuModelRegistry |
| `src/hashcat_bench/parser.py` | Parse hashcat `--machine-readable` and `nvidia-smi` output |
| `src/hashcat_bench/data.py` | DataManager: result I/O, idempotency, index building |
| `src/hashcat_bench/provider.py` | VastProvider: Vast.ai SDK wrapper |
| `src/hashcat_bench/estimator.py` | CostEstimator: pricing queries and cost math |
| `src/hashcat_bench/runner.py` | BenchmarkRunner: SSH into instances, run container, collect JSON |
| `src/hashcat_bench/cli.py` | CLI entrypoint with argparse subcommands |
| `container/Dockerfile` | Benchmark container build |
| `container/entrypoint.sh` | Runs hashcat, outputs JSON to stdout + /tmp/result.json |
| `site/src/App.svelte` | Main dashboard app |
| `site/src/lib/*.svelte` | FilterBar, TableView, CompareView, ExportButton |
| `data/gpu-models.json` | Canonical GPU model list |
| `data/results/**/*.json` | Benchmark result files |
