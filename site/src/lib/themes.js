export const THEMES = {
  dark: {
    bg: '#0f172a',
    'bg-surface': '#1e293b',
    'bg-elevated': '#334155',
    text: '#e2e8f0',
    'text-muted': '#94a3b8',
    'text-dim': '#64748b',
    accent: '#818cf8',
    'accent-hover': '#a5b4fc',
    'accent-bg': 'rgba(129, 140, 248, 0.15)',
    border: '#334155',
    'border-subtle': '#1e293b',
    'row-alt': 'rgba(30, 41, 59, 0.5)',
    danger: '#f87171',
    success: '#34d399',
  },
  light: {
    bg: '#f8fafc',
    'bg-surface': '#ffffff',
    'bg-elevated': '#e2e8f0',
    text: '#1e293b',
    'text-muted': '#64748b',
    'text-dim': '#94a3b8',
    accent: '#6366f1',
    'accent-hover': '#4f46e5',
    'accent-bg': 'rgba(99, 102, 241, 0.1)',
    border: '#cbd5e1',
    'border-subtle': '#e2e8f0',
    'row-alt': 'rgba(241, 245, 249, 0.8)',
    danger: '#ef4444',
    success: '#16a34a',
  },
  dracula: {
    bg: '#282a36',
    'bg-surface': '#44475a',
    'bg-elevated': '#6272a4',
    text: '#f8f8f2',
    'text-muted': '#bfc7d5',
    'text-dim': '#6272a4',
    accent: '#bd93f9',
    'accent-hover': '#d4b8ff',
    'accent-bg': 'rgba(189, 147, 249, 0.15)',
    border: '#6272a4',
    'border-subtle': '#44475a',
    'row-alt': 'rgba(68, 71, 90, 0.5)',
    danger: '#ff5555',
    success: '#50fa7b',
  },
  'catppuccin-mocha': {
    bg: '#1e1e2e',
    'bg-surface': '#313244',
    'bg-elevated': '#45475a',
    text: '#cdd6f4',
    'text-muted': '#a6adc8',
    'text-dim': '#6c7086',
    accent: '#cba6f7',
    'accent-hover': '#ddbfff',
    'accent-bg': 'rgba(203, 166, 247, 0.15)',
    border: '#45475a',
    'border-subtle': '#313244',
    'row-alt': 'rgba(49, 50, 68, 0.5)',
    danger: '#f38ba8',
    success: '#a6e3a1',
  },
  'catppuccin-latte': {
    bg: '#eff1f5',
    'bg-surface': '#e6e9ef',
    'bg-elevated': '#ccd0da',
    text: '#4c4f69',
    'text-muted': '#6c6f85',
    'text-dim': '#9ca0b0',
    accent: '#8839ef',
    'accent-hover': '#7029cf',
    'accent-bg': 'rgba(136, 57, 239, 0.1)',
    border: '#ccd0da',
    'border-subtle': '#e6e9ef',
    'row-alt': 'rgba(230, 233, 239, 0.6)',
    danger: '#d20f39',
    success: '#40a02b',
  },
  'tokyo-night': {
    bg: '#1a1b26',
    'bg-surface': '#24283b',
    'bg-elevated': '#414868',
    text: '#a9b1d6',
    'text-muted': '#7982a9',
    'text-dim': '#565f89',
    accent: '#7aa2f7',
    'accent-hover': '#89b4fa',
    'accent-bg': 'rgba(122, 162, 247, 0.15)',
    border: '#414868',
    'border-subtle': '#24283b',
    'row-alt': 'rgba(36, 40, 59, 0.5)',
    danger: '#f7768e',
    success: '#9ece6a',
  },
  'github-dark': {
    bg: '#0d1117',
    'bg-surface': '#161b22',
    'bg-elevated': '#21262d',
    text: '#e6edf3',
    'text-muted': '#7d8590',
    'text-dim': '#484f58',
    accent: '#58a6ff',
    'accent-hover': '#79c0ff',
    'accent-bg': 'rgba(88, 166, 255, 0.15)',
    border: '#30363d',
    'border-subtle': '#21262d',
    'row-alt': 'rgba(22, 27, 34, 0.5)',
    danger: '#f85149',
    success: '#3fb950',
  },
  'github-light': {
    bg: '#ffffff',
    'bg-surface': '#f6f8fa',
    'bg-elevated': '#eaeef2',
    text: '#1f2328',
    'text-muted': '#656d76',
    'text-dim': '#8b949e',
    accent: '#0969da',
    'accent-hover': '#0550ae',
    'accent-bg': 'rgba(9, 105, 218, 0.08)',
    border: '#d0d7de',
    'border-subtle': '#e8e8e8',
    'row-alt': 'rgba(246, 248, 250, 0.8)',
    danger: '#d1242f',
    success: '#1a7f37',
  },
};

export const THEME_META = {
  dark: { name: 'Dark', group: 'dark' },
  dracula: { name: 'Dracula', group: 'dark' },
  'catppuccin-mocha': { name: 'Catppuccin Mocha', group: 'dark' },
  'tokyo-night': { name: 'Tokyo Night', group: 'dark' },
  'github-dark': { name: 'GitHub Dark', group: 'dark' },
  light: { name: 'Light', group: 'light' },
  'catppuccin-latte': { name: 'Catppuccin Latte', group: 'light' },
  'github-light': { name: 'GitHub Light', group: 'light' },
};

const LIGHT_THEMES = new Set(['light', 'catppuccin-latte', 'github-light']);

export function applyTheme(themeId) {
  const vars = THEMES[themeId];
  if (!vars) return;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(vars)) {
    root.style.setProperty(`--${key}`, value);
  }
  root.style.setProperty(
    'color-scheme',
    LIGHT_THEMES.has(themeId) ? 'light' : 'dark'
  );
  localStorage.setItem('hashcat-bench-theme', themeId);
}

export function getInitialTheme() {
  const saved = localStorage.getItem('hashcat-bench-theme');
  if (saved && THEMES[saved]) return saved;
  if (window.matchMedia('(prefers-color-scheme: light)').matches) return 'light';
  return 'dark';
}
