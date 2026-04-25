import './app.css';
import { getInitialTheme, applyTheme } from './lib/themes.js';

applyTheme(getInitialTheme());

import App from './App.svelte';
import { mount } from 'svelte';

const app = mount(App, { target: document.getElementById('app') });

export default app;
