<script>
  let {
    versions = [],
    gpuModels = [],
    selectedVersion = $bindable(''),
    selectedGpus = $bindable([]),
    hashModeQuery = $bindable('')
  } = $props();

  function toggleGpu(model) {
    if (selectedGpus.includes(model)) {
      selectedGpus = selectedGpus.filter(g => g !== model);
    } else {
      selectedGpus = [...selectedGpus, model];
    }
  }
</script>

<div class="filter-bar">
  <div class="filter-group">
    <label class="filter-label" for="version-select">Hashcat Version</label>
    <select id="version-select" class="filter-select" bind:value={selectedVersion}>
      <option value="">All versions</option>
      {#each versions as v}
        <option value={v}>{v}</option>
      {/each}
    </select>
  </div>

  <div class="filter-group filter-group--gpus">
    <span class="filter-label">GPU Models</span>
    <div class="gpu-chips">
      {#each gpuModels as model}
        <button
          type="button"
          class="gpu-chip"
          class:gpu-chip--active={selectedGpus.includes(model)}
          onclick={() => toggleGpu(model)}
        >
          {model}
        </button>
      {/each}
    </div>
  </div>

  <div class="filter-group">
    <label class="filter-label" for="hash-search">Hash Mode</label>
    <input
      id="hash-search"
      type="text"
      class="filter-input"
      placeholder="Search by name or number..."
      bind:value={hashModeQuery}
    />
  </div>
</div>
