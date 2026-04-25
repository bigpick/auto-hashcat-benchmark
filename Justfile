set dotenv-load

python := "uv run"
data_dir := "data"

# --- Setup ---

setup:
    uv sync --all-extras
    cd site && npm install
    {{ python }} pre-commit install

# --- Tests ---

test *ARGS:
    {{ python }} pytest tests/ {{ ARGS }}

test-cov:
    {{ python }} pytest tests/ --cov=hashcat_bench --cov-report=term-missing

lint *ARGS:
    {{ python }} pre-commit run {{ ARGS }}

# --- Discovery ---

list-gpus *FILTER:
    {{ python }} hashcat-bench list-gpus {{ if FILTER != "" { "--filter " + FILTER } else { "" } }}

# --- Cost Estimation ---

estimate GPU HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} estimate --gpu {{ GPU }} --hashcat {{ HASHCAT }}

estimate-matrix HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} estimate-matrix --hashcat {{ HASHCAT }}

# --- Container ---

registry := env("HASHCAT_BENCH_REGISTRY", "ghcr.io/YOUR_USERNAME/hashcat-bench")

build-image HASHCAT_VERSION:
    docker build \
        --build-arg HASHCAT_VERSION={{ HASHCAT_VERSION }} \
        -t {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2 \
        container/

push-image HASHCAT_VERSION:
    docker push {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2

# --- Benchmarking ---

bench GPU HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench --gpu {{ GPU }} --hashcat {{ HASHCAT }}

bench-matrix HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench-matrix --hashcat {{ HASHCAT }}

bench-matrix-capped HASHCAT BUDGET:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench-matrix --hashcat {{ HASHCAT }} --budget-cap {{ BUDGET }}

# --- Data ---

build-index:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} build-index

validate:
    {{ python }} -c "from hashcat_bench.data import DataManager; from pathlib import Path; dm = DataManager(Path('{{ data_dir }}')); [print(f'OK: {r.hashcat_version}/{r.gpu_model}') for r in dm.load_all_results()]"

status HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} status --versions {{ HASHCAT }}

# --- Frontend ---

dev:
    cd site && npm run dev

build-site: build-index
    cp {{ data_dir }}/index.json site/public/index.json
    cd site && npm run build
