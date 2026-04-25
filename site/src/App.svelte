<script>
  import { loadIndex, filterResults } from './lib/data.js';
  import FilterBar from './lib/FilterBar.svelte';
  import TableView from './lib/TableView.svelte';
  import CompareView from './lib/CompareView.svelte';
  import ExportButton from './lib/ExportButton.svelte';
  import ThemePicker from './lib/ThemePicker.svelte';

  let index = $state(null);
  let loading = $state(true);
  let error = $state(null);

  let selectedVersion = $state('');
  let selectedGpus = $state([]);
  let hashModeQuery = $state('');
  let activeTab = $state('table');

  // Load data on mount
  $effect(() => {
    loadIndex()
      .then(data => {
        index = data;
        loading = false;
      })
      .catch(err => {
        error = err.message;
        loading = false;
      });
  });

  // Filtered data
  let filtered = $derived.by(() => {
    if (!index) return { results: [], hashModes: [] };
    return filterResults(index, {
      version: selectedVersion,
      gpuModels: selectedGpus,
      hashModeQuery
    });
  });
</script>

<header class="app-header">
  <div class="app-header-row">
    <div class="app-header-spacer"></div>
    <div class="app-header-center">
      <h1 class="app-title">Hashcat GPU Benchmarks</h1>
      <p class="app-subtitle">Compare GPU hashing performance across models and versions</p>
    </div>
    <div class="app-header-end">
      <ThemePicker />
    </div>
  </div>
</header>

{#if loading}
  <div class="loading">Loading benchmark data...</div>
{:else if error}
  <div class="error">Failed to load data: {error}</div>
{:else}
  <div class="toolbar">
    <FilterBar
      versions={index.versions}
      gpuModels={index.gpu_models}
      bind:selectedVersion
      bind:selectedGpus
      bind:hashModeQuery
    />
    <ExportButton hashModes={filtered.hashModes} results={filtered.results} />
  </div>

  <div class="tab-bar">
    <button
      type="button"
      class="tab-btn"
      class:tab-btn--active={activeTab === 'table'}
      onclick={() => activeTab = 'table'}
    >
      Table View
    </button>
    <button
      type="button"
      class="tab-btn"
      class:tab-btn--active={activeTab === 'compare'}
      onclick={() => activeTab = 'compare'}
    >
      Compare View
    </button>
  </div>

  <main class="main-content">
    {#if activeTab === 'table'}
      <TableView hashModes={filtered.hashModes} results={filtered.results} />
    {:else}
      <CompareView hashModes={filtered.hashModes} results={filtered.results} />
    {/if}
  </main>

  <footer class="app-footer">
    <p>
      Generated {index.generated_at ? new Date(index.generated_at).toLocaleDateString() : ''}
      &middot; {index.results.length} benchmark result{index.results.length !== 1 ? 's' : ''}
    </p>
  </footer>
{/if}
