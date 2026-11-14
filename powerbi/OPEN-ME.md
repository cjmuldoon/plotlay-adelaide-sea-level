# Opening the Power BI report

`AdelaideSeaLevel.pbip` is a Power BI Project: the report (`AdelaideSeaLevel.Report`, PBIR format) and the semantic model (`AdelaideSeaLevel.SemanticModel`, TMDL) saved as text, so the repo can show every change. Power BI Desktop opens it like a `.pbix`.

## What you need

- Power BI Desktop for Windows, a recent version (2026). If Desktop is older than about mid 2025, turn on **File, Options and settings, Options, Preview features, Power BI Project (.pbip) save option** and **Store reports using enhanced metadata format (PBIR)**, then restart Desktop.
- The repo folder on the Windows machine.

## Open it

1. In Windows, open File Explorer and go to the repo's `powerbi` folder.
2. Double-click `AdelaideSeaLevel.pbip`, or in Desktop: **File, Open report, Browse reports**, file type *Power BI project files (\*.pbip)*.
3. The visuals are empty the first time. Select **Refresh** on the Home ribbon.
   - By default the data is read from the repo's public copy on GitHub (`DataFolder` is `https://raw.githubusercontent.com/cjmuldoon/plotlay-adelaide-sea-level/main/data/`). If Desktop asks how to connect, choose **Anonymous** and **Connect**.
   - To read the files on disk instead: **Home, Transform data, Edit parameters**, set `DataFolder` to the full path of the repo's `data` folder **ending with a backslash**, then **OK** and **Apply changes**.
   - If Desktop warns about privacy levels, choose **Ignore privacy levels** for this file (all sources are public open data) or set them to Public.
4. Check the numbers (below).

If the report was updated while open, close Power BI and reopen the .pbip rather than using Apply external changes.

## Check the numbers after Refresh

After **Refresh**:

| Page | Visual | Should read |
|---|---|---|
| Levels | Residential addresses below each grounded level | Highest tide today 134, Highest tide + 0.3 m 158, Highest tide + 1.0 m 12,698, 1-in-100-year storm tide + 0.3 m 19,066, 1-in-100-year storm tide + 1.0 m 34,993 |
| Suburbs | Below 2.4 m AHD (card) | 12,698 |
| Suburbs | Below 3.4 m AHD (card) | 34,993 |

On **Suburbs**, West Lakes tops the bar chart (2,893). The suburb cards add up the suburbs, so they can differ by a few from the totals on the Levels page (addresses outside any ABS suburb).

## The map

- **Shape Map** (Suburbs page). The custom map is saved inside the report (`AdelaideSeaLevel.Report/StaticResources/RegisteredResources/`), a copy of `data/geometry/suburbs.topojson` keyed by the ABS suburb code, so the suburbs draw on open, shaded by their residential addresses below 2.4 m AHD. The Shape Map has no base map of its own, so the saved file also carries pale context round the suburbs (ABS suburbs, CC BY 4.0). The water itself is not on the Shape Map (it draws one value per area); the heights are in `data/heights/` for Python or QGIS.
- If the map shows the United States instead (an older Desktop can ignore a saved map): select the map, **Format visual**, **Visual**, **Map settings**, **Map type: Custom map**, **Add map type**, and choose `..\data\geometry\suburbs.topojson`. If the Shape Map is not in the Visualizations pane at all, turn it on in **File, Options and settings, Options, Preview features, Shape map visual** and restart Desktop.
- If the Shape Map comes up empty after opening, drag the fields back: Location `Suburbs[sal_code]`, Color saturation `[Below 2.4 m]`.

## What the numbers are

A height-based picture, not a flood or coastal model: ground below a level of still water that the sea can reach, from Geoscience Australia's 5 m LiDAR heights (metres AHD, about ±0.3 m at best). It leaves out tides, storm surge, waves, erosion, sea walls and levees the heights do not show, and drainage. An address is not a person or a building. Residents are the 2021 Census counts of each mesh block, shared by the part of its ground below the level.
