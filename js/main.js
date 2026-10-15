/*
  main.js
  Loads every Vega-Lite chart into its <div> on the page.
  Each chart's full specification lives in /specs as a readable .vg.json file;
  this file only says WHICH spec goes in WHICH div and sets a shared look (theme).
*/

// ---------- Shared theme ----------
// One config object applied to every chart, so fonts, sizes and colours match
// across the page (instead of repeating the same settings in 11 JSON files).
const FONT = '"Source Sans 3", "Source Sans Pro", Arial, sans-serif';
const INK = '#1E1E1E';
const MUTED = '#5A5A50';
const GRID = '#E6E1D3';

const theme = {
  background: null,                       // transparent: the page/panel colour shows through
  font: FONT,
  view: { stroke: null },                 // no box around each chart (better data-ink ratio)
  axis: {
    labelFont: FONT, titleFont: FONT,
    labelFontSize: 11, titleFontSize: 12,
    labelColor: MUTED, titleColor: MUTED, titleFontWeight: 'normal',
    domainColor: '#B9B4A6', tickColor: '#B9B4A6', gridColor: GRID
  },
  legend: {
    labelFont: FONT, titleFont: FONT, labelFontSize: 11, titleFontSize: 12,
    labelColor: MUTED, titleColor: MUTED, titleFontWeight: 'normal'
  },
  header: { labelFont: FONT, titleFont: FONT },
  text: { font: FONT },
  title: { font: FONT },
  autosize: { type: 'fit', contains: 'padding' }   // charts shrink to their container: no horizontal scrolling
};

// The pictogram sits on the dark green hero, so its labels are light and its sacks are mustard.
const heroTheme = {
  ...theme,
  axis: { ...theme.axis, labelColor: '#F3EEDF' },
  point: { color: '#E3B94A' },
  text: { font: FONT, color: '#F3EEDF' }
};

// ---------- Which spec goes in which div ----------
const charts = [
  { id: '#vis-pictogram',  spec: 'specs/01_pictogram.vg.json', config: heroTheme },
  { id: '#vis-line',       spec: 'specs/02_line_index.vg.json' },
  { id: '#vis-heatmap',    spec: 'specs/03_heatmap_industries.vg.json' },
  { id: '#vis-waterfall',  spec: 'specs/04_waterfall_growth.vg.json' },
  { id: '#vis-inputs',     spec: 'specs/05_input_types.vg.json' },
  { id: '#vis-choropleth', spec: 'specs/06_choropleth_states.vg.json' },
  { id: '#vis-barmap',     spec: 'specs/07_bar_symbol_map.vg.json' },
  { id: '#vis-bump',       spec: 'specs/08_bump_ranks.vg.json' },
  { id: '#vis-climate',    spec: 'specs/09_climate_adjusted_line.vg.json' },
  { id: '#vis-slope',      spec: 'specs/10_slope_states.vg.json' },
  { id: '#vis-flow',       spec: 'specs/11_flow_exports.vg.json' }
];

// ---------- Draw them ----------
charts.forEach(({ id, spec, config }) => {
  vegaEmbed(id, spec, {
    config: config || theme,
    actions: false,        // hide the "..." export menu; the JSON files are in /specs for anyone who wants them
    renderer: 'svg'        // SVG keeps text sharp at any zoom level
  }).catch(err => {
    // If a chart fails, say so in the page instead of leaving a blank box.
    document.querySelector(id).textContent = 'This chart could not load: ' + err.message;
    console.error(spec, err);
  });
});
