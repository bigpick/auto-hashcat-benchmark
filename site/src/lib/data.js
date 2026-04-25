export async function loadIndex() {
  const res = await fetch('./index.json');
  return res.json();
}

export function filterResults(index, { version, gpuModels, hashModeQuery }) {
  let results = index.results;
  if (version) {
    results = results.filter(r => r.hashcat_version === version);
  }
  if (gpuModels && gpuModels.length > 0) {
    results = results.filter(r => gpuModels.includes(r.gpu_model));
  }
  let hashModes = index.hash_modes;
  if (hashModeQuery) {
    const q = hashModeQuery.toLowerCase();
    hashModes = hashModes.filter(
      m => m.name.toLowerCase().includes(q) || String(m.mode).includes(q)
    );
  }
  return { results, hashModes };
}
