export function formatSpeed(hashesPerSecond) {
  if (hashesPerSecond >= 1e12) return (hashesPerSecond / 1e12).toFixed(1) + ' TH/s';
  if (hashesPerSecond >= 1e9) return (hashesPerSecond / 1e9).toFixed(1) + ' GH/s';
  if (hashesPerSecond >= 1e6) return (hashesPerSecond / 1e6).toFixed(1) + ' MH/s';
  if (hashesPerSecond >= 1e3) return (hashesPerSecond / 1e3).toFixed(1) + ' kH/s';
  return hashesPerSecond + ' H/s';
}
