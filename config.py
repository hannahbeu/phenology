"""Settings shared by all notebooks. The year range and the AOI are set here only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- years
# Every download and analysis covers FIRST_YEAR..LAST_YEAR (years in the future are skipped).
FIRST_YEAR = 2017
LAST_YEAR = 2026
YEARS = list(range(FIRST_YEAR, LAST_YEAR + 1))
START, END = f"{FIRST_YEAR}-01-01", f"{LAST_YEAR}-12-31"

# ---------------------------------------------------------------- AOI
# GeoTIFF mask (non-zero pixels of AOI_RASTER_BAND, or the pixel values in AOI_RASTER_VALUES) or a
# vector file (.geojson/.shp/.gpkg) in AOI_FOLDER. Other mask in the folder:
# "Larch_Classification_2017_threshold099.tif"
DATA_DIR = ROOT / "data"                               # input files: AOI masks (aoi/), validation data (validation/)
AOI_FOLDER = DATA_DIR / "aoi"
AOI_FILE = "Larch_Classification_2017_multidate_aspect_improved_threshold099.tif"
AOI_RASTER_VALUES = None
AOI_RASTER_BAND = 1

AOI_PATH = AOI_FOLDER / AOI_FILE
AOI_NAME = AOI_PATH.stem
CACHE_DIR = ROOT / "cache" / f"{AOI_NAME}_zones"       # Sentinel-2 statistics per year and zone (notebook 01)
SITE_CACHE_DIR = ROOT / "cache" / f"{AOI_NAME}_sites"  # the same for the areas around SITE_AREAS (notebook 01 §6)
CLIMATE_SOURCE_DIR = ROOT / "cache" / "climate" / "sources"   # clipped climate data, shared by all AOIs (03)
CLIMATE_DIR = ROOT / "cache" / "climate" / AOI_NAME    # zone series of this AOI (notebook 03)
VALIDATION_DIR = ROOT / "cache" / "validation" / AOI_NAME   # MeteoSwiss larch observations (notebook 02)
OUT_DIR = ROOT / "results" / AOI_NAME                  # phenology results (notebook 04)
CLIMATE_OUT_DIR = OUT_DIR / "climate"                  # climate analysis results (notebook 05)

# ---------------------------------------------------------------- Sentinel-2 (01) and date filter (04)
RESOLUTION = 10            # m
INNER_BUFFER = 0           # m; shrink the AOI to avoid mixed edge pixels (0 = off)
SCL_KEEP = [4, 5]          # SCL classes counted as clear: 4 vegetation, 5 bare soil
# SCL class groups whose share of the zone is stored per date
SCL_GROUPS = {
    "nodata": [0, 1],      # no data / saturated or defective
    "dark": [2],           # dark area pixels, incl. topographic shadow
    "shadow": [3],         # cloud shadow
    "water": [6],
    "unclassified": [7],
    "cloud": [8, 9],       # cloud medium / high probability
    "cirrus": [10],
    "snow": [11],
}
MAX_SCENE_CLOUD = 100      # % tile cloud cover (100 = no limit)
MAX_SCL_FRACTION = {"cloud": 1.0, "cirrus": 1.0, "shadow": 1.0, "snow": 1.0, "nodata": 1.0}   # 1.0 = no limit
MIN_VALID_FRACTION = 0.15  # share of clear pixels in the zone needed to keep a date
# What the clear and SCL shares (MIN_VALID_FRACTION, MAX_SCL_FRACTION, GOOD_VALID_FRACTION, MAX_SNOW_FRACTION) refer to:
# "covered" = the zone pixels inside the scene's footprint, so scenes from the swath edge that cover only part of a
# zone can pass; "zone" = all zone pixels (the original behaviour)
VALID_SHARE_OF = "covered"
MIN_COVERED_PIXELS = 200   # zone pixels a scene must cover to be used

# Topographic zones: elevation band x north/south facing (+ flat)
DEM_COLLECTION = "cop-dem-glo-30"
ELEV_STEP = 200            # m
FLAT_SLOPE = 5             # degrees
MIN_ZONE_PIXELS = 200

# ---------------------------------------------------------------- phenology metrics (04)
# 04 skips indices the cache lacks; 01 re-downloads years whose CSV lacks one (REFRESH_MISSING_INDICES)
INDICES = ["NDVI", "GRVI", "PSRI", "RCC"]
SMOOTH_WINDOW = 7          # 5-day steps -> centred 35-day moving average
AUTUMN_START_DOY = 182     # 1 Jul: autumn observations run from here to the end of POST_WINDOW
MIN_OBS_PER_YEAR = 6       # weighted autumn observations needed for a double-logistic fit
# Direction of the autumn change: greenness drops, PSRI / RCC rise with yellowing
EXPECT_DECREASE = {"NDVI": True, "GRVI": True, "PSRI": False, "RCC": False}
ALPHA = 0.05
# A year counts only once its cache reaches this DOY (1 Dec); earlier = autumn still in progress at download time
SEASON_COMPLETE_DOY = 335

# ---------------------------------------------------------------- season dates: start / peak / end (04 §3-6)
# Two candidates per date type, "<method> / <index> / <metric>": method = Whittaker | double logistic,
# metric = start | mid | end (see AMPLITUDE_FRACTIONS). The peak is the 50 % point ("mid") of the autumn change.
SEASON_METHODS = {
    "start": ["Whittaker / GRVI / start", "double logistic / GRVI / start"],
    "peak": ["Whittaker / GRVI / mid", "double logistic / NDVI / mid"],
    "end": ["Whittaker / GRVI / end", "double logistic / NDVI / end"],
}
# Dates at a share of the autumn amplitude still left: 90 % = start of the decline ("senescence" in MODIS
# MCD12Q2), 50 % = midpoint (MCD12Q2 "greendown midpoint"), 15 % = end (HR-VPP end of season, MCD12Q2 dormancy)
AMPLITUDE_FRACTIONS = {"start": 0.9, "mid": 0.5, "end": 0.15}
SUMMER_WINDOW = (182, 243) # DOY Jul-Aug: summer level of the Whittaker dates
POST_WINDOW = (305, 334)   # DOY Nov: post-season level after needle fall, before lasting snow (Beck et al. 2006)
MIN_BASE_OBS = 5           # snow-free clear dates in POST_WINDOW (all years) needed; fewer -> the whole AOI's level
SEASON_WINDOW = (91, 334)  # DOY range of the double-logistic fit (Apr-Nov)
MAX_SNOW_FRACTION = 0.2    # dates with a larger snow share of the zone get weight 0
GOOD_VALID_FRACTION = 0.5  # clear share for weight 1; below: weight 0.5 (HR-VPP weight classes)
OUTLIER_FACTOR = 6         # outlier: residual > 6x the global and the local median residual (HR-VPP)
WHITTAKER_LAMBDAS = [1e1, 3e1, 1e2, 3e2, 1e3, 3e3, 1e4, 3e4, 1e5]   # candidates, chosen by cross-validation

# ---------------------------------------------------------------- validation data (02) and comparison (04 §7)
VALIDATION_RADIUS_KM = 40  # MeteoSwiss stations and local sites with larch observations within this distance
PHENO_PARAMS = {"mlard94d": "needle colouring 50 %", "mlard95d": "needle drop 50 %"}   # European larch
LOCAL_PHENO_FILE = DATA_DIR / "validation" / "Lärchen_pheno.xlsx"   # local larch observations per site, year and phase (LV95 coordinates)
REFERENCE_FOREST_FILE = DATA_DIR / "validation" / "Lärchen_SNP.shp" # forest-type map (polygons, column Forest_typ) to check the AOI against (02)
# Site check (01 §6, 04 §7c): Sentinel-2 statistics of the AOI pixels within SITE_RADIUS_M of these local sites
# (site codes of LOCAL_PHENO_FILE), compared with the site's own observations
SITE_AREAS = ["fuo"]
SITE_RADIUS_M = 500

# ---------------------------------------------------------------- chosen dates and projection (04 §7-9)
# Date used per date type for the projection, the topography and 05: "average" = mean of both candidates of
# SEASON_METHODS, or one of them, e.g. "Whittaker / GRVI / mid"
SEASON_CHOICE = {"start": "average", "peak": "average", "end": "average"}
FORECAST_YEARS = 2         # years projected ahead with the OLS trend
# ---------------------------------------------------------------- climate data (03)
# MeteoSwiss gridded observations (1 km, LV95): variable -> product
OBS_GRID_PRODUCTS = {"tas": "tabsd", "tasmin": "tmind", "tasmax": "tmaxd", "pr": "rhiresd", "srel": "sreld"}
CLIMATE_SPINUP_DAYS = 92   # observations also downloaded for the last days of FIRST_YEAR - 1
GRID_BUFFER = 2000         # m around the AOI when clipping grids
LAPSE_RATE_FALLBACK = -0.0065   # K/m, used if the lapse rate cannot be fitted from the grid

TEMPERATURE_VARS = ["tas", "tasmin", "tasmax"]   # shifted to each zone's elevation with the lapse rate

# CH2025 climate scenarios (30-year daily series per global warming level, 26 model chains)
CH2025_PERIODS = ["ref91-20", "gwl1.5", "gwl2.0", "gwl2.5", "gwl3.0"]
CH2025_GRID_VARS = ["tas", "tasmin", "tasmax", "pr"]
CH2025_GRID_MODELS = None  # None = all model chains, or a list such as ["clmcom-cclm4-cccma"]

# ---------------------------------------------------------------- climate analysis (05)
# Phenology dates to explain/predict: "start" | "peak" | "end" = the chosen dates of 04 (SEASON_CHOICE,
# season_selected.csv), or one candidate of SEASON_METHODS, e.g. "Whittaker / GRVI / mid" (season_dates.csv)
TARGETS = ["start", "peak", "end"]
