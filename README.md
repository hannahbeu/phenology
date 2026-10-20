# Larch autumn phenology from Sentinel-2

Dates of the autumn yellowing of European larch (start, peak and end) for 2017–2026, derived from Sentinel-2 per topographic zone (elevation band × aspect) of a larch area of interest (AOI), and related to climate observations and CH2025 climate scenarios. Study area: around the MeteoSwiss station Buffalora (Val Müstair / Swiss National Park).

## Workflow

The notebooks run in order. Each one reads the output of the earlier ones from `cache/` or `results/`.

| Notebook | What it does | Writes |
|---|---|---|
| `01_download_sentinel2` | Sentinel-2 L2A from Microsoft Planetary Computer (no account needed). Splits the AOI into zones using the Copernicus DEM; NDVI, GRVI, PSRI and RCC statistics of the clear pixels per date and zone | `cache/<AOI>_zones/` |
| `02_download_validation` | MeteoSwiss larch observations (needle colouring 50 %, needle drop 50 %) near the AOI | `cache/validation/<AOI>/` |
| `03_download_climate` | MeteoSwiss gridded and station observations, CH2025 local and gridded scenarios; daily series per zone, with lapse-rate correction | `cache/climate/sources/`, `cache/climate/<AOI>/` |
| `04_phenology_metrics` | Date filtering; Whittaker and double-logistic curves; start / peak / end per zone and year; method comparison against the validation data; trend; topography effects | `results/<AOI>/` |
| `05_climate_analysis` | Zone fixed-effects regression of the dates on climate features; projection with CH2025 per global warming level, compared with the trend | `results/<AOI>/climate/` |

`01` and `03` take hours on the first run (the CH2025 grid alone is 512 files of ~1.8 GB). After that they only fetch what is missing. `04` and `05` run offline in a few minutes.

## Setup

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
nbstripout --install          # notebooks are committed without outputs
```

- **AOI:** the AOI files are in `aoi/`: larch classification GeoTIFFs (non-zero pixels = larch). A vector file (.geojson/.shp/.gpkg) also works. Choose one with `AOI_FILE` in `config.py`.

## Configuration

All settings are in `config.py`. The main ones:

- `FIRST_YEAR`, `LAST_YEAR`: the year range for all notebooks
- `AOI_FILE`: which AOI to process. Every AOI gets its own folders in `cache/` and `results/`.
- `SEASON_INDICES`, `SEASON_CHOICE`: the indices each date type is read from, and which method's date (or the average of both) is used downstream
- `TARGETS`: the date types that `05` analyses

Shared helper functions are in `phenology_utils.py`.

## Repository layout

```
config.py, phenology_utils.py   settings and shared functions
0*_*.ipynb                      the workflow notebooks
aoi/                            AOI masks (larch classification GeoTIFFs)
cache/<AOI>_zones/              Sentinel-2 statistics per year (stats_<year>.csv), zones.csv / zones.tif
cache/validation/<AOI>/         MeteoSwiss phenology observations
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
- MeteoSwiss open data: gridded observations (`ogd-surface-derived-grid`), SwissMetNet station Buffalora (`ogd-smn`) and phenology observations (`ogd-phenology`)
- MeteoSwiss & ETH Zurich (2025): Climate CH2025 – Daily Datasets (local and gridded)

The methods and literature are described in the notebooks.
