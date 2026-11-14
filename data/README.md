# Data

- `tables/levels.csv`: one row per level. `kind` grounded (from published tides and allowances) or illustration (0 to 10 m by 0.5 m). `land_ha`: land (ground above 0 m AHD) below the level and reachable from the sea. `mean_depth_m`, `max_depth_m`: depth of water over that land. `addresses`, `residential_addresses` (with `residential_*` by depth band at the address): G-NAF principal addresses whose ground is below the level. `residents_2021`, `dwellings_2021`: ABS 2021 Census mesh block counts shared by area.
- `tables/levels_landuse.csv`: hectares below each level by Data.SA land use class.
- `tables/levels_roads.csv` (ODbL): km of OpenStreetMap road below each level, `all` and by `highway` class; bridges left out.
- `tables/suburbs.csv`: residential addresses in each ABS suburb (`sal_code`) and those below each grounded level.
- `tables/sources.csv`: the grounded levels, how each is worked out and where from.
- `tables/summary.json`: the area, the grid, the settings, totals, the everything-below comparison and the note.
- `geometry/meshblocks.geojson`: ABS mesh blocks (2021) in the area with `category`, `persons`, `dwellings`, `suburb`; simplified by 2.5 m.
- `geometry/suburbs.*`: the ABS suburbs in the area with their counts; simplified by 5 m.
- `heights/ground_height_4m_ahd.tif` (zoom 14) and `ground_height_8m_ahd.tif` (zoom 13): Float32, EPSG:3857, metres AHD.
