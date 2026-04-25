<script>
  import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
  import { formatSpeed } from './format.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

  let { hashModes = [], results = [] } = $props();

  let selectedMode = $state(null);
  let canvasEl = $state(null);
  let chartInstance = $state(null);

  // Set initial selected mode when hash modes load
  $effect(() => {
    if (hashModes.length > 0 && selectedMode === null) {
      selectedMode = hashModes[0].mode;
    }
  });

  // Data for the selected hash mode
  let chartData = $derived.by(() => {
    if (selectedMode === null) return { labels: [], speeds: [] };
    const labels = [];
    const speeds = [];
    for (const r of results) {
      const b = r.benchmarks.find(b => b.hash_mode === selectedMode);
      if (b) {
        labels.push(r.gpu_model);
        speeds.push(b.speed);
      }
    }
    return { labels, speeds };
  });

  // Comparison text
  let comparisonText = $derived.by(() => {
    const { labels, speeds } = chartData;
    if (labels.length < 2) return '';
    let maxIdx = 0;
    let minIdx = 0;
    for (let i = 1; i < speeds.length; i++) {
      if (speeds[i] > speeds[maxIdx]) maxIdx = i;
      if (speeds[i] < speeds[minIdx]) minIdx = i;
    }
    if (speeds[minIdx] === 0) return '';
    const ratio = (speeds[maxIdx] / speeds[minIdx]).toFixed(1);
    return `${labels[maxIdx]} is ${ratio}x faster than ${labels[minIdx]}`;
  });

  // Chart colors
  const COLORS = [
    'rgba(129, 140, 248, 0.8)',
    'rgba(52, 211, 153, 0.8)',
    'rgba(251, 191, 36, 0.8)',
    'rgba(248, 113, 113, 0.8)',
    'rgba(167, 139, 250, 0.8)',
    'rgba(96, 165, 250, 0.8)',
  ];

  // Render / update chart
  $effect(() => {
    if (!canvasEl) return;
    const { labels, speeds } = chartData;

    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }

    if (labels.length === 0) return;

    chartInstance = new Chart(canvasEl, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Speed',
          data: speeds,
          backgroundColor: labels.map((_, i) => COLORS[i % COLORS.length]),
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => formatSpeed(ctx.raw)
            }
          }
        },
        scales: {
          x: {
            ticks: {
              color: '#94a3b8',
              callback: (v) => formatSpeed(v)
            },
            grid: { color: 'rgba(148, 163, 184, 0.1)' }
          },
          y: {
            ticks: { color: '#e2e8f0' },
            grid: { display: false }
          }
        }
      }
    });
  });
</script>

<div class="compare-view">
  <div class="compare-controls">
    <label class="filter-label" for="mode-select">Hash Mode</label>
    <select id="mode-select" class="filter-select" bind:value={selectedMode}>
      {#each hashModes as hm}
        <option value={hm.mode}>{hm.mode} - {hm.name}</option>
      {/each}
    </select>
  </div>

  <div class="chart-container">
    <canvas bind:this={canvasEl}></canvas>
  </div>

  {#if comparisonText}
    <p class="comparison-text">{comparisonText}</p>
  {/if}
</div>
