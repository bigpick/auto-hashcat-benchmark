<script>
  import { formatSpeed } from './format.js';

  let { hashModes = [], results = [] } = $props();

  let sortKey = $state('mode');
  let sortAsc = $state(true);

  // Build a map: gpu_model -> { hash_mode -> speed }
  let speedMap = $derived.by(() => {
    const map = {};
    for (const r of results) {
      if (!map[r.gpu_model]) map[r.gpu_model] = {};
      for (const b of r.benchmarks) {
        map[r.gpu_model][b.hash_mode] = b.speed;
      }
    }
    return map;
  });

  // Unique GPU names from filtered results
  let gpuNames = $derived.by(() => {
    const seen = new Set();
    const names = [];
    for (const r of results) {
      if (!seen.has(r.gpu_model)) {
        seen.add(r.gpu_model);
        names.push(r.gpu_model);
      }
    }
    return names;
  });

  // Sorted rows
  let sortedModes = $derived.by(() => {
    const rows = [...hashModes];
    rows.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'mode') {
        cmp = a.mode - b.mode;
      } else if (sortKey === 'name') {
        cmp = a.name.localeCompare(b.name);
      } else {
        // sortKey is a gpu_model name
        const sa = speedMap[sortKey]?.[a.mode] ?? 0;
        const sb = speedMap[sortKey]?.[b.mode] ?? 0;
        cmp = sa - sb;
      }
      return sortAsc ? cmp : -cmp;
    });
    return rows;
  });

  function handleSort(key) {
    if (sortKey === key) {
      sortAsc = !sortAsc;
    } else {
      sortKey = key;
      sortAsc = true;
    }
  }

  function sortIndicator(key) {
    if (sortKey !== key) return '';
    return sortAsc ? ' ▲' : ' ▼';
  }
</script>

<div class="table-wrapper">
  <table class="bench-table">
    <thead>
      <tr>
        <th class="col-mode" onclick={() => handleSort('mode')}>
          Mode{sortIndicator('mode')}
        </th>
        <th class="col-name" onclick={() => handleSort('name')}>
          Hash Type{sortIndicator('name')}
        </th>
        {#each gpuNames as gpu}
          <th class="col-speed" onclick={() => handleSort(gpu)}>
            {gpu}{sortIndicator(gpu)}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each sortedModes as hm}
        <tr>
          <td class="col-mode">{hm.mode}</td>
          <td class="col-name">{hm.name}</td>
          {#each gpuNames as gpu}
            {@const speed = speedMap[gpu]?.[hm.mode]}
            <td class="col-speed" title={speed != null ? speed.toLocaleString() + ' H/s' : ''}>
              {speed != null ? formatSpeed(speed) : '-'}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
