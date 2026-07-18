// Chart tokens validated with the dataviz palette checker against #0b0e14.
export const SERIES = ["#C4820A", "#1E9BC4", "#2AA95F", "#9D63EA", "#E05C8F"];
export const LOSS_LINE = "#FFB224"; // single-series live curve, bright signal amber
export const GRID = "#232c3d";
export const AXIS_TEXT = "#8b96a8";
export const TOOLTIP_STYLE = {
  backgroundColor: "#1a2130",
  border: "1px solid #33405a",
  borderRadius: 8,
  fontSize: 12,
  fontFamily: '"IBM Plex Mono", monospace',
  color: "#e8edf5",
} as const;

/** Sequential single-hue ramp (dark → cyan) for the confusion-matrix heatmap. */
export function heatColor(value: number, max: number): string {
  const t = max > 0 ? value / max : 0;
  const from = { r: 0x16, g: 0x20, b: 0x2e };
  const to = { r: 0x4c, g: 0xc9, b: 0xf0 };
  const mix = (a: number, b: number) => Math.round(a + (b - a) * t);
  return `rgb(${mix(from.r, to.r)}, ${mix(from.g, to.g)}, ${mix(from.b, to.b)})`;
}
