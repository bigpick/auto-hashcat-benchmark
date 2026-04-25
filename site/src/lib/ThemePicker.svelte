<script>
  import { THEMES, THEME_META, applyTheme } from './themes.js';

  let open = $state(false);
  let currentTheme = $state(localStorage.getItem('hashcat-bench-theme') || 'dark');
  let pickerEl = $state(null);

  let currentName = $derived(THEME_META[currentTheme]?.name ?? 'Dark');

  let basicThemes = $derived(
    Object.entries(THEME_META).filter(([, m]) => m.group === 'basic')
  );
  let popularThemes = $derived(
    Object.entries(THEME_META).filter(([, m]) => m.group === 'popular')
  );

  function select(id) {
    applyTheme(id);
    currentTheme = id;
    open = false;
  }

  function toggle() {
    open = !open;
  }

  function handleClickOutside(e) {
    if (pickerEl && !pickerEl.contains(e.target)) {
      open = false;
    }
  }

  $effect(() => {
    if (open) {
      document.addEventListener('click', handleClickOutside, true);
    }
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  });
</script>

<div class="theme-picker" bind:this={pickerEl}>
  <button type="button" class="theme-picker-btn" onclick={toggle}>
    <svg class="theme-picker-icon" viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
      <path fill-rule="evenodd" d="M7.455 2.004a.75.75 0 01.26.77 7.047 7.047 0 009.511 9.511.75.75 0 011.03 1.03A8.547 8.547 0 117.224 1.744a.75.75 0 01.23.26z" clip-rule="evenodd" />
    </svg>
    <span class="theme-picker-label">{currentName}</span>
    <svg class="theme-picker-caret" viewBox="0 0 20 20" fill="currentColor" width="12" height="12">
      <path fill-rule="evenodd" d="M5.22 8.22a.75.75 0 011.06 0L10 11.94l3.72-3.72a.75.75 0 111.06 1.06l-4.25 4.25a.75.75 0 01-1.06 0L5.22 9.28a.75.75 0 010-1.06z" clip-rule="evenodd" />
    </svg>
  </button>

  {#if open}
    <div class="theme-dropdown">
      <div class="theme-group-label">Basic</div>
      {#each basicThemes as [id, meta]}
        <button
          type="button"
          class="theme-option"
          class:theme-option--active={currentTheme === id}
          onclick={() => select(id)}
        >
          <span class="theme-swatch" style:background={THEMES[id].accent}></span>
          {meta.name}
        </button>
      {/each}

      <div class="theme-group-label">Popular</div>
      {#each popularThemes as [id, meta]}
        <button
          type="button"
          class="theme-option"
          class:theme-option--active={currentTheme === id}
          onclick={() => select(id)}
        >
          <span class="theme-swatch" style:background={THEMES[id].accent}></span>
          {meta.name}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .theme-picker {
    position: relative;
  }

  .theme-picker-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    font-size: 0.8rem;
    font-weight: 500;
    font-family: var(--sans);
    color: var(--text-muted);
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .theme-picker-btn:hover {
    color: var(--text);
    border-color: var(--accent);
  }

  .theme-picker-icon {
    flex-shrink: 0;
  }

  .theme-picker-caret {
    flex-shrink: 0;
    opacity: 0.6;
  }

  .theme-picker-label {
    line-height: 1;
  }

  .theme-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    min-width: 180px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 4px;
    z-index: 100;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }

  .theme-group-label {
    padding: 6px 10px 4px;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
  }

  .theme-option {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 7px 10px;
    font-size: 0.8rem;
    font-family: var(--sans);
    color: var(--text);
    background: transparent;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.1s;
    text-align: left;
  }

  .theme-option:hover {
    background: var(--bg-elevated);
  }

  .theme-option--active {
    color: var(--accent);
    font-weight: 600;
  }

  .theme-swatch {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }
</style>
