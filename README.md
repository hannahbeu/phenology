# Larch autumn phenology from Sentinel-2

Dates of the autumn yellowing of European larch (start, peak and end) for 2017–2026, derived from Sentinel-2 per topographic zone (elevation band × aspect) of a larch area of interest (AOI), and related to climate observations and CH2025 climate scenarios. Study area: the larch stands of the Swiss National Park.

## Workflow

The notebooks run in order. Each one reads the output of the earlier ones from `cache/` or `results/`.

| Notebook | What it does | Writes |
|---|---|---|
| `01_download_sentinel2` | Sentinel-2 L2A from Microsoft Planetary Computer (no account needed). Splits the AOI into zones using the Copernicus DEM; NDVI, GRVI, PSRI and RCC statistics of the clear pixels per date and zone; the same for the AOI pixels around local sites (`SITE_AREAS`) | `cache/<AOI>_zones/`, `cache/<AOI>_sites/` |
| `02_download_validation` | Larch observations (needle colouring 50 %, needle drop 50 %) near the AOI from two separate sources: MeteoSwiss stations and the local sites of `Lärchen_pheno.xlsx`; maps of the stations, sites and the Swiss National Park; checks of the larch classification against the forest-type map `Lärchen_SNP.shp` and against images | `cache/validation/<AOI>/` |
| `03_download_climate` | MeteoSwiss gridded observations and CH2025 gridded scenarios; daily series per zone, with lapse-rate correction | `cache/climate/sources/`, `cache/climate/<AOI>/` |
| `04_phenology_metrics` | Date filtering; Whittaker and double-logistic curves; start / peak / end per zone and year; method comparison against the validation data; check against a local site's own observations; trend; topography effects | `results/<AOI>/` |
| `05_climate_analysis` | Zone fixed-effects regression of the dates on climate features; projection with CH2025 per global warming level, compared with the trend | `results/<AOI>/climate/` |

`01` and `03` take hours on the first run (the CH2025 grid alone is 512 files of ~1.8 GB). After that they only fetch what is missing. `04` and `05` run offline in a few minutes.

## Setup

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
nbstripout --install          # notebooks are committed without outputs
```

- **Input files** are in `data/`. The AOI files are in `data/aoi/`: larch classification GeoTIFFs (non-zero pixels = larch). A vector file (.geojson/.shp/.gpkg) also works. Choose one with `AOI_FILE` in `config.py`. The local validation data are in `data/validation/`: the larch observations `Lärchen_pheno.xlsx` and the forest-type map `Lärchen_SNP.shp`.

## Configuration

All settings are in `config.py`. The main ones:

- `FIRST_YEAR`, `LAST_YEAR`: the year range for all notebooks
- `AOI_FILE`: which AOI to process. Every AOI gets its own folders in `cache/` and `results/`.
- `LOCAL_PHENO_FILE`, `SITE_AREAS`, `SITE_RADIUS_M`: the local larch observations, and the sites whose surrounding AOI pixels get their own dates for a direct check
- `SEASON_METHODS`, `SEASON_CHOICE`: the two date candidates per date type, and which one (or their average) is used downstream
- `TARGETS`: the date types that `05` analyses

Shared helper functions are in `phenology_utils.py`.

## Repository layout

```
config.py, phenology_utils.py   settings and shared functions
0*_*.ipynb                      the workflow notebooks
data/aoi/                       AOI masks (larch classification GeoTIFFs)
data/validation/                local larch observations (Lärchen_pheno.xlsx), forest-type map (Lärchen_SNP.shp)
cache/<AOI>_zones/              Sentinel-2 statistics per year (stats_<year>.csv), zones.csv / zones.tif
cache/<AOI>_sites/              the same for the areas around SITE_AREAS
cache/validation/<AOI>/         MeteoSwiss and local phenology observations, maps (stations, AOI checks)
cache/climate/                  climate data (not in git: too large; rebuilt by 03)
results/<AOI>/                  season dates, method comparison, projection, topography effects
results/<AOI>/climate/          climate effects, regression, CH2025 projections
```

Two AOIs have been processed:
- `Larch_Classification_2017_multidate_aspect_improved_threshold099` (the current default)
- `Larch_Classification_2017_threshold099`

## Notes

- **Incomplete years:** a year whose Sentinel-2 cache ends before 1 December (`SEASON_COMPLETE_DOY`) counts as preliminary. `04` and `05` leave it out of all tables and models. To include the current year once its autumn is over, delete its `stats_<year>.csv` and re-run `01`.
- **Cache settings:** the Sentinel-2 cache is valid only for the settings stored in `settings.json`. `01` refuses to mix caches built with different settings.
- **CH2025 projections:** the scenarios are not forecasts of specific years. They describe 30-year climate states at a global warming level of +1.5 to +3.0 °C, from 26 regional model chains. Two chains do not reach +3.0 °C.

## Data sources

- Sentinel-2 L2A and Copernicus DEM GLO-30, via Microsoft Planetary Computer
- MeteoSwiss open data: gridded observations (`ogd-surface-derived-grid`) and phenology observations (`ogd-phenology`)
- MeteoSwiss & ETH Zurich (2025): Climate CH2025 – Daily Datasets (gridded)
- Local larch phenology observations (`Lärchen_pheno.xlsx`): Il Fuorn, Val Cluozza, Val Mingèr, Val Trupchun, Lü
- Forest-type map of the Swiss National Park area (`Lärchen_SNP.shp`)
- swisstopo: national map (grey), SWISSIMAGE, terrain height service; BAFU: Swiss National Park border

The methods and literature are described in the notebooks.
