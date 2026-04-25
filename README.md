<div align="center">

# ⚡ Hashcat GPU Benchmarks

**Apples-to-apples GPU speed benchmarks for [hashcat](https://github.com/hashcat/hashcat)**

[![Build](https://img.shields.io/github/actions/workflow/status/bigpick/auto-hashcat-benchmark/deploy.yml?branch=main&style=flat-square&label=build)](https://github.com/bigpick/auto-hashcat-benchmark/actions)
[![Python](https://img.shields.io/badge/python-3.12+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Svelte](https://img.shields.io/badge/svelte-5-ff3e00?style=flat-square&logo=svelte&logoColor=white)](https://svelte.dev/)
[![GPUs](https://img.shields.io/badge/GPUs-101-f59e0b?style=flat-square)]()
[![Vast.ai](https://img.shields.io/badge/powered%20by-vast.ai-6366f1?style=flat-square)](https://vast.ai)

[**Live Dashboard**](https://bigpick.github.io/auto-hashcat-benchmark) · [Development Guide](DEVELOPMENT.md) · [Request a GPU](https://github.com/bigpick/auto-hashcat-benchmark/issues/new)

</div>

---

## The problem

Hashcat benchmark results are all over the place - gists, forum threads, random wiki pages. Every one of them uses a different hashcat version, different drivers, different OS. Comparing GPU performance across these is a guessing game.

This project runs every benchmark inside the same Docker container (same hashcat build, same CUDA toolkit, same OS) so the GPU is the only thing that changes. The results go to a filterable web dashboard where you can sort by hash mode, compare GPUs side by side, and export the data.

## How it works

```
┌─── Your machine ──────────────────────────────────────────┐
│  just bench rtx-4090 v6.2.6                               │
│    → Search Vast.ai for cheapest RTX 4090                 │
│    → Rent instance, run Docker container                  │
│    → Collect JSON results, destroy instance                │
│    → Save to data/results/v6.2.6/rtx-4090.json           │
└───────────────────────────────────────────────────────────┘
          │ git push
          ▼
┌─── GitHub Actions ────────────────────────────────────────┐
│  Build index.json → Build Svelte site → Deploy to Pages   │
└───────────────────────────────────────────────────────────┘
```

The orchestrator checks for existing results before renting anything. If a result already exists for that hashcat version + GPU + kernel mode, it skips it.

## Quick start

```bash
just setup                        # install everything
just list-gpus                    # check GPU availability and prices
just estimate-matrix v6.2.6       # cost estimate (no money spent)
just bench rtx-4090 v6.2.6        # run one benchmark
just dev                          # preview the dashboard locally
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full setup walkthrough.

## GPU coverage

| Series | Models |
|--------|--------|
| **RTX 50** (Blackwell) | 5090, 5080, 5070 Ti, 5070 |
| **RTX 40** (Ada Lovelace) | 4090, 4080, 4070 Ti, 4070, 4060 Ti, 4060 |
| **RTX 30** (Ampere) | 3090, 3080, 3070, 3060 |

RTX 10/20 series, AMD, and datacenter GPUs (A100, H100) can be added if they are available on Vast.ai at a reasonable price. [Open an issue](https://github.com/bigpick/auto-hashcat-benchmark/issues/new) to request one.

## The dashboard

Two views, same filter bar.

**Table** - every hash mode as a row, selected GPUs as columns. Sortable. Speeds show as GH/s or MH/s with the raw number on hover. Works fine with 300+ hash modes.

**Compare** - pick a hash mode, get a bar chart of GPU speeds. Tells you things like "RTX 4090 is 2.0x faster than RTX 3080" so you don't have to do the math.

You can filter by hashcat version, toggle GPUs on and off, search hash modes by name or number, and export whatever you are looking at as CSV or JSON.

<details>
<summary>Tech stack</summary>
<br>

Python 3.12+ ([uv](https://docs.astral.sh/uv/)) · [Vast.ai](https://vast.ai) SDK · Docker on nvidia/cuda · Svelte 5 + Vite + Chart.js · [Just](https://github.com/casey/just) · GitHub Actions · GitHub Pages

</details>

<details>
<summary>Security</summary>
<br>

All secrets live in environment variables, never in source. A [ripsecrets](https://github.com/sirwart/ripsecrets) pre-commit hook blocks commits that contain anything that looks like a key or token. `.env` files are gitignored - see `.env.example` for what you need to set.

</details>

## License

TBD
