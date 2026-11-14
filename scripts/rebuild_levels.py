"""Rebuild the counts under each water level from the heights, the mesh blocks and G-NAF, independently of Plotlay.

  python scripts/rebuild_levels.py            (from the repository's top folder; a few minutes)

Reads data/heights/ground_height_4m_ahd.tif (Plotlay's terrain tiles at zoom 14: Geoscience Australia's 5 m LiDAR DEM
via Mapterhorn, metres AHD, Web Mercator) and data/geometry/meshblocks.geojson (ABS mesh blocks with their 2021 Census
residents), downloads the G-NAF August 2026 address points for the area from Plotlay's public copy of the release (the
same pieces the Plotlay app reads; no list of addresses is kept), and writes work/rebuilt_levels.csv to compare with
data/tables/levels.csv.

The method, written out here in plain Python so it can be checked line by line:
  1. Connected to the sea: water starts from the cells on the north, west and south edges at or below 0 m AHD (the
     gulf and the Port River mouth) and spreads to the 8 cells around each cell. Each cell gets the lowest water
     level that reaches it (a priority flood): the highest ground on the lowest path from the sea.
  2. Under a level L: the cells whose level is at or below L. Land: the cells whose ground is above 0 m.
  3. An address counts when the cell under its point is under the water; residential when its mesh block's 2021
     category is Residential.
  4. Residents: each mesh block's residents shared by the part of its cells under the water.
"""
import gzip, heapq, io, json, math, os, sys, urllib.request
import numpy as np, pandas as pd, tifffile
from matplotlib.path import Path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *a: os.path.join(HERE, *a)
LEVELS = [1.4, 1.7, 2.4, 2.7, 3.4] + [x / 2 for x in range(0, 21)]
BASE = 'https://plotlay-data.cjmuldoon.workers.dev/boundaries/v1/au/gnaf/2026-08/'

# 1. the heights and where each cell is
with tifffile.TiffFile(D('data/heights/ground_height_4m_ahd.tif')) as t:
    z = t.pages[0].asarray().astype(np.float64)
    scale = t.pages[0].tags['ModelPixelScaleTag'].value; tie = t.pages[0].tags['ModelTiepointTag'].value
H, W = z.shape
x0, y0, cx, cy = tie[3], tie[4], scale[0], scale[1]
R = 6378137.0
lat_rows = np.degrees(2 * np.arctan(np.exp((y0 - (np.arange(H) + 0.5) * cy) / R)) - np.pi / 2)
cell_m2 = cx * cy * np.cos(np.radians(lat_rows)) ** 2          # Web Mercator metres shrink by cos(latitude) each way

# the priority flood
fill = np.full(H * W, np.inf); done = np.zeros(H * W, bool); zf = z.ravel(); heap = []
seeds = [(0, c) for c in range(W)] + [(H - 1, c) for c in range(W)] + [(r, 0) for r in range(H)]
for r, c in seeds:
    i = r * W + c
    if not done[i] and zf[i] <= 0: done[i] = True; fill[i] = zf[i]; heap.append((zf[i], i))
heapq.heapify(heap)
nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
while heap:
    k, i = heapq.heappop(heap); r, c = divmod(i, W)
    for dr, dc in nb:
        rr, cc = r + dr, c + dc
        if 0 <= rr < H and 0 <= cc < W:
            j = rr * W + cc
            if not done[j]:
                done[j] = True; kk = zf[j] if zf[j] > k else k; fill[j] = kk; heapq.heappush(heap, (kk, j))
fill = fill.reshape(H, W)
print('flooded the grid', file=sys.stderr)

def cell_of(lat, lng):
    x = np.radians(lng) * R; y = np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)) * R
    return np.floor((y0 - y) / cy).astype(int), np.floor((x - x0) / cx).astype(int)

# 3. addresses: G-NAF's pieces for the postcodes listed in summary.json
summ = json.load(open(D('data/tables/summary.json')))
S, Wd, N, E = summ['area']['south'], summ['area']['west'], summ['area']['north'], summ['area']['east']
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'plotlay-adelaide-sea-level rebuild'}), timeout=120).read()
loc = pd.read_csv(io.BytesIO(gzip.decompress(get(BASE + 'localities.csv.gz'))), dtype=str, keep_default_na=False)
chunks = sorted(set(loc[loc.postcode.isin(summ['postcodes'])].chunk))
a = pd.concat([pd.read_csv(io.BytesIO(gzip.decompress(get(BASE + c))), dtype=str, keep_default_na=False) for c in chunks]).drop_duplicates('pid')
a = a[a.alias == 'P']; a['lat'] = a.lat.astype(float); a['lon'] = a.lon.astype(float)
a = a[(a.lat >= S) & (a.lat <= N) & (a.lon >= Wd) & (a.lon <= E)].copy()
mb = json.load(open(D('data/geometry/meshblocks.geojson')))['features']
cat = {}; paths = []
for f in mb:
    g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    for poly in polys:
        paths.append((f['properties']['code'], f['properties']['category'], f['properties']['persons'] or 0, len(polys), [Path(np.array(r)) for r in poly]))
# each address's mesh block (its point inside the outline), for Residential
pts = a[['lon', 'lat']].to_numpy(); a['cat'] = None
for code, category, persons, nparts, rings in paths:
    b = rings[0].get_extents(); sel = (pts[:, 0] >= b.x0) & (pts[:, 0] <= b.x1) & (pts[:, 1] >= b.y0) & (pts[:, 1] <= b.y1)
    if not sel.any(): continue
    idx = np.where(sel)[0]; inside = rings[0].contains_points(pts[idx])
    for h in rings[1:]: inside &= ~h.contains_points(pts[idx])
    a.iloc[idx[inside], a.columns.get_loc('cat')] = category
ar, ac = cell_of(a.lat.to_numpy(), a.lon.to_numpy())
ok = (ar >= 0) & (ar < H) & (ac >= 0) & (ac < W)
a_lv = np.where(ok, fill[np.clip(ar, 0, H - 1), np.clip(ac, 0, W - 1)], np.inf)
res = a['cat'].to_numpy() == 'Residential'

# 4. each mesh block part's cells (centres inside), sorted by level, for the residents' share
parts = []
cols_x = x0 + (np.arange(W) + 0.5) * cx; rows_y = y0 - (np.arange(H) + 0.5) * cy
lng_cols = np.degrees(cols_x / R)
for code, category, persons, nparts, rings in paths:
    b = rings[0].get_extents()
    c0, c1 = np.searchsorted(lng_cols, [b.x0, b.x1]); r0 = np.searchsorted(-lat_rows, -b.y1); r1 = np.searchsorted(-lat_rows, -b.y0)
    if c1 <= c0 or r1 <= r0: parts.append((persons / nparts, np.array([]), np.array([]), 1.0)); continue
    gx, gy = np.meshgrid(lng_cols[c0:c1], lat_rows[r0:r1]); q = np.c_[gx.ravel(), gy.ravel()]
    inside = rings[0].contains_points(q)
    for h in rings[1:]: inside &= ~h.contains_points(q)
    lv = fill[r0:r1, c0:c1].ravel()[inside]; am = np.repeat(cell_m2[r0:r1], c1 - c0)[inside]
    o = np.argsort(lv); parts.append((persons / nparts, lv[o], np.cumsum(am[o]), am.sum() or 1.0))
land = z > 0
rows = []
for L in LEVELS:
    wet = fill <= L
    land_ha = float((cell_m2[:, None] * (wet & land)).sum() / 1e4)
    people = sum(p * (cum[np.searchsorted(lv, L, side='right') - 1] / tot if np.searchsorted(lv, L, side='right') else 0) for p, lv, cum, tot in parts)
    rows.append({'level_m_ahd': L, 'land_ha': round(land_ha), 'addresses': int((a_lv <= L).sum()), 'residential_addresses': int(((a_lv <= L) & res).sum()), 'residents': round(people)})
os.makedirs(D('work'), exist_ok=True)
out = pd.DataFrame(rows).drop_duplicates('level_m_ahd').sort_values('level_m_ahd')
out.to_csv(D('work/rebuilt_levels.csv'), index=False)
print(out.to_string(index=False))
