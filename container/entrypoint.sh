#!/usr/bin/env bash
set -euo pipefail

KERNEL_MODE="${KERNEL_MODE:-optimized}"
HASHCAT_VERSION="${HASHCAT_VERSION:-unknown}"
CONTAINER_IMAGE="${CONTAINER_IMAGE:-unknown}"
CUDA_VERSION="${CUDA_VERSION:-12.9.1}"

# Find the hashcat binary (system-installed or local in /root/hashcat)
if command -v hashcat &>/dev/null; then
    HASHCAT_BIN="hashcat"
elif [ -x /root/hashcat/hashcat ]; then
    HASHCAT_BIN="/root/hashcat/hashcat"
else
    echo "ERROR: hashcat binary not found" >&2
    exit 1
fi

gpu_info=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader)
gpu_name=$(echo "$gpu_info" | cut -d',' -f1 | xargs)
driver_version=$(echo "$gpu_info" | cut -d',' -f2 | xargs)

hashcat_flags="-b --machine-readable"
if [ "$KERNEL_MODE" = "optimized" ]; then
    hashcat_flags="$hashcat_flags -O"
fi

benchmark_output=$($HASHCAT_BIN $hashcat_flags 2>/dev/null || true)

benchmark_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

benchmarks_json=$(echo "$benchmark_output" | grep -v '^#' | grep -v '^$' | while IFS=: read -r dev_id _f1 hash_mode exec_ms _f2 speed; do
    exec_sec=$(echo "scale=1; $exec_ms / 1000" | bc)
    printf '{"hash_mode":%s,"hash_name":"mode_%s","speed":%s,"exec_runtime_ms":%s}\n' \
        "$hash_mode" "$hash_mode" "$speed" "$exec_sec"
done | jq -s '.')

jq -n \
    --arg hv "$HASHCAT_VERSION" \
    --arg gm "$gpu_name" \
    --arg ci "$CONTAINER_IMAGE" \
    --arg dv "$driver_version" \
    --arg cv "$CUDA_VERSION" \
    --arg km "$KERNEL_MODE" \
    --arg bd "$benchmark_date" \
    --argjson bm "$benchmarks_json" \
    '{
        hashcat_version: $hv,
        gpu_model: $gm,
        container_image: $ci,
        driver_version: $dv,
        cuda_version: $cv,
        kernel_mode: $km,
        benchmark_date: $bd,
        benchmarks: $bm
    }' | tee /tmp/result.json
