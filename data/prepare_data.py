"""
prepare_data.py
Turns the ABARES workbook into small, tidy CSV files that the Vega-Lite charts read.
Run once from the repository root:  python3 data/prepare_data.py
Only reshapes, renames and (where noted) does simple arithmetic on ABARES numbers.
"""
import csv, openpyxl

WB = openpyxl.load_workbook('data/raw/Data_AustAgPrdctvty2024-25_v1_1_0.xlsx',
                            read_only=True, data_only=True)
OUT = 'data/'
STATES = ['New South Wales', 'Victoria', 'Queensland', 'South Australia',
          'Western Australia', 'Tasmania', 'Northern Territory']
ABBR = dict(zip(STATES, ['NSW', 'Vic', 'Qld', 'SA', 'WA', 'Tas', 'NT']))

def table(name):
    """Return (header row, data rows) for one sheet, skipping the title row."""
    rows = list(WB[name].iter_rows(values_only=True))
    return rows[1], [r for r in rows[2:] if r[0] not in (None, '')]

def num(v):
    """ABARES uses 'nr' (not reported) and 'na'; turn those into blanks."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return ''

def write(fname, fields, rows):
    # Typography: a year range like 1977-78 is written with an en-dash (1977–78)
    for r in rows:
        if 'fy' in r:
            r['fy'] = r['fy'].replace('-', '\u2013')
    with open(OUT + fname, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print('wrote', fname, len(rows), 'rows')

def start_year(fy):
    """'1977-78' -> 1977 (first calendar year of the financial year)."""
    return int(fy[:4])

# ---------- 1. National index, All industries + climate-adjusted (tables 1 and c1) ----------
_, t1 = table('table_1')
_, c1 = table('table_c1')
actual = {r[0]: r[1] for r in t1}
adjusted = {r[0]: r[1] for r in c1}
base_a, base_c = actual['1988-89'], adjusted['1988-89']
rows = []
for fy, v in actual.items():
    row = {'fy': fy, 'year': start_year(fy), 'index': v,
           # Rebased to 1988-89 = 100 so the two series can share one axis
           # (ABARES says the climate-adjusted index is NOT 100 in its first year).
           'actual_rebased': '', 'adjusted_rebased': '', 'adjusted_raw': ''}
    if fy in adjusted:
        row['actual_rebased'] = round(v / base_a * 100, 1)
        row['adjusted_rebased'] = round(adjusted[fy] / base_c * 100, 1)
        row['adjusted_raw'] = adjusted[fy]
    rows.append(row)
write('national_index.csv', list(rows[0].keys()), rows)

# Worst seasons: years where actual / climate-adjusted is lowest
# (i.e. where ABARES's own weather adjustment says the season hurt most).
ratio = sorted((actual[fy] / adjusted[fy], fy) for fy in adjusted)
print('lowest actual/adjusted ratios:', [(fy, round(r, 3)) for r, fy in ratio[:6]])

# ---------- 2. Industry index by year (tables 2-6 + dairy 16), All Australia column ----------
rows = []
for sheet, ind in [('table_2', 'Cropping'), ('table_3', 'Mixed crop-livestock'),
                   ('table_5', 'Beef'), ('table_6', 'Sheep-beef'),
                   ('table_4', 'Sheep'), ('table_16', 'Dairy')]:
    _, d = table(sheet)
    for r in d:
        rows.append({'industry': ind, 'fy': r[0], 'year': start_year(r[0]), 'index': num(r[1])})
write('industry_index.csv', ['industry', 'fy', 'year', 'index'], rows)

# ---------- 3. Growth decomposition (tables 7, 8, 9), All Australia column ----------
labels = {'All industries': 'All broadacre', 'Cropping': 'Cropping', 'Mixed': 'Mixed crop-livestock',
          'Beef': 'Beef', 'Sheep-Beef': 'Sheep-beef', 'Sheep': 'Sheep'}
_, t7 = table('table_7'); _, t8 = table('table_8'); _, t9 = table('table_9')
tfp = {r[0]: r for r in t7}; inp = {r[0]: r for r in t8}; out = {r[0]: r for r in t9}
rows = []
for key, lab in labels.items():
    rows.append({'industry': lab, 'output_growth': num(out[key][1]),
                 'input_growth': num(inp[key][1]), 'productivity_growth': num(tfp[key][1])})
write('growth_decomposition.csv', ['industry', 'output_growth', 'input_growth', 'productivity_growth'], rows)

# ---------- 4. Input growth by type (table 10) ----------
hdr, t10 = table('table_10')
rows = []
for r in t10:
    for i, typ in enumerate(hdr[1:], start=1):
        rows.append({'industry': labels[r[0]], 'input_type': typ, 'growth': num(r[i])})
write('input_types.csv', ['industry', 'input_type', 'growth'], rows)

# ---------- 5. State growth rates by industry (table 7 + dairy table 17) ----------
hdr, _ = table('table_7')
_, t17 = table('table_17')
rows = []
for key, lab in labels.items():
    for i, st in enumerate(hdr[1:], start=1):
        if st in STATES:
            rows.append({'industry': lab, 'state': st, 'abbr': ABBR[st], 'growth': num(tfp[key][i])})
hdr17, _ = table('table_17')
for i, st in enumerate(hdr17[1:], start=1):
    if st in STATES:
        rows.append({'industry': 'Dairy', 'state': st, 'abbr': ABBR[st], 'growth': num(t17[0][i])})
# Dairy has no NT column in ABARES table 17 -> mark as not reported
rows.append({'industry': 'Dairy', 'state': 'Northern Territory', 'abbr': 'NT', 'growth': ''})
write('state_growth.csv', ['industry', 'state', 'abbr', 'growth'], rows)

# ---------- 6. State output vs input growth, All industries (tables 8, 9) ----------
# lon/lat = where the bar symbol stands on the map (chosen by the author, roughly
# the middle of the farming area of each state, so bars do not overlap).
anchor = {'New South Wales': (147.0, -32.0), 'Victoria': (143.0, -37.4),
          'Queensland': (145.0, -23.5), 'South Australia': (136.0, -31.0),
          'Western Australia': (120.5, -28.5), 'Tasmania': (148.3, -42.3),
          'Northern Territory': (133.5, -20.0)}
hdr, _ = table('table_8')
rows = []
for i, st in enumerate(hdr[1:], start=1):
    if st in STATES:
        lon, lat = anchor[st]
        rows.append({'state': st, 'abbr': ABBR[st], 'lon': lon, 'lat': lat,
                     'output_growth': num(out['All industries'][i]),
                     'input_growth': num(inp['All industries'][i]),
                     'productivity_growth': num(tfp['All industries'][i])})
write('state_output_input.csv', list(rows[0].keys()), rows)

# ---------- 7. State ranks by period (table 1) ----------
hdr, _ = table('table_1')
periods = [('1977–89', 1977, 1989), ('1990s', 1990, 1999), ('2000s', 2000, 2009),
           ('2010s', 2010, 2019), ('2020–24', 2020, 2024)]
rows = []
for label, a, b in periods:
    avgs = []
    for i, st in enumerate(hdr[1:], start=1):
        if st not in STATES:
            continue
        vals = [r[i] for r in t1 if a <= start_year(r[0]) <= b]
        avgs.append((sum(vals) / len(vals), st))
    for rank, (v, st) in enumerate(sorted(avgs, reverse=True), start=1):
        rows.append({'period': label, 'state': st, 'abbr': ABBR[st], 'avg_index': round(v, 1), 'rank': rank})
write('state_ranks.csv', ['period', 'state', 'abbr', 'avg_index', 'rank'], rows)

# ---------- 8. Climate-adjusted change by state, rebased 1988-89 = 100 (table c1, c7) ----------
hdr, _ = table('table_c1')
_, c7 = table('table_c7')
rate = {st: num(c7[0][i]) for i, st in enumerate(hdr[1:], start=1)}
first, last = c1[0], c1[-1]
rows = []
for i, st in enumerate(hdr[1:], start=1):
    name = 'All Australia' if st == 'All Australia' else st
    rows.append({'state': name, 'abbr': ABBR.get(st, 'Aus'), 'fy': first[0], 'point': 'start',
                 'raw': first[i], 'rebased': 100, 'growth_rate': rate[st]})
    rows.append({'state': name, 'abbr': ABBR.get(st, 'Aus'), 'fy': last[0], 'point': 'end',
                 'raw': last[i], 'rebased': round(last[i] / first[i] * 100, 1), 'growth_rate': rate[st]})
write('climate_adjusted_states.csv', ['state', 'abbr', 'fy', 'point', 'raw', 'rebased', 'growth_rate'], rows)

# ---------- 9. Curved flow lines for the flow map (from data/exports.csv) ----------
# exports.csv holds the DFAT figures typed in by the author. Each flow becomes 25 points
# along a gentle curve (a quadratic Bezier curve) from Australia to the market, so the
# flows fan out instead of overlapping near Australia (curved flows are easier to tell
# apart on origin-destination flow maps). The curve shape is decoration only; the data
# is the line width (value_m).
import math
ORIGIN = (134.0, -25.5)
with open(OUT + 'exports.csv') as f:
    markets = list(csv.DictReader(f))
rows = []
for m in markets:
    lon, lat = float(m['lon']), float(m['lat'])
    if lon < 0:
        lon += 360          # United States: go east across the Pacific, not west across Africa
    x0, y0 = ORIGIN
    dx, dy = lon - x0, lat - y0
    # control point: the midpoint pushed sideways by 20% of the flow length.
    # Malaysia's flow bends the other way so it does not pass over Indonesia's dot.
    bend = -1 if m['country'] == 'Malaysia' else 1
    cx, cy = x0 + dx / 2 + bend * 0.2 * dy, y0 + dy / 2 - bend * 0.2 * dx
    for i in range(25):
        s = i / 24
        x = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s ** 2 * lon
        y = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cy + s ** 2 * lat
        rows.append({'country': m['country'], 'value_m': m['value_m'], 'share': m['share'],
                     'rank': m['rank'], 'step': i, 'lon': round(x if x <= 180 else x - 360, 3), 'lat': round(y, 3)})
write('exports_paths.csv', ['country', 'value_m', 'share', 'rank', 'step', 'lon', 'lat'], rows)
