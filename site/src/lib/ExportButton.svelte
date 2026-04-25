<script>
  import { formatSpeed } from './format.js';

  let { hashModes = [], results = [] } = $props();

  function buildSpeedMap() {
    const map = {};
    for (const r of results) {
      if (!map[r.gpu_model]) map[r.gpu_model] = {};
      for (const b of r.benchmarks) {
        map[r.gpu_model][b.hash_mode] = b.speed;
      }
    }
    return map;
  }

  function getGpuNames() {
    const seen = new Set();
    const names = [];
    for (const r of results) {
      if (!seen.has(r.gpu_model)) {
        seen.add(r.gpu_model);
        names.push(r.gpu_model);
      }
    }
    return names;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function exportCSV() {
    const gpuNames = getGpuNames();
    const speedMap = buildSpeedMap();
    const header = ['Mode', 'Hash Type', ...gpuNames].join(',');
    const rows = hashModes.map(hm => {
      const speeds = gpuNames.map(gpu => speedMap[gpu]?.[hm.mode] ?? '');
      return [hm.mode, `"${hm.name}"`, ...speeds].join(',');
    });
    const csv = [header, ...rows].join('\n');
    downloadBlob(new Blob([csv], { type: 'text/csv' }), 'hashcat-benchmarks.csv');
  }

  function exportJSON() {
    const gpuNames = getGpuNames();
    const speedMap = buildSpeedMap();
    const data = hashModes.map(hm => {
      const entry = { mode: hm.mode, name: hm.name };
      for (const gpu of gpuNames) {
        entry[gpu] = speedMap[gpu]?.[hm.mode] ?? null;
      }
      return entry;
    });
    const json = JSON.stringify(data, null, 2);
    downloadBlob(new Blob([json], { type: 'application/json' }), 'hashcat-benchmarks.json');
  }
</script>

<div class="export-buttons">
  <button type="button" class="export-btn" onclick={exportCSV}>Export CSV</button>
  <button type="button" class="export-btn" onclick={exportJSON}>Export JSON</button>
</div>
