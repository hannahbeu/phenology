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
# "Larch_Classification_2017_multidate_aspect_improved_threshold099.tif"
AOI_FOLDER = Path(r"C:\Users\hanna\OneDrive\Desktop\Documents\Uni\HS 26\GIS Exkursion\project")
AOI_FILE = "Larch_Classification_2017_threshold099.tif"
AOI_RASTER_VALUES = None
AOI_RASTER_BAND = 1

AOI_PATH = AOI_FOLDER / AOI_FILE
AOI_NAME = AOI_PATH.stem
CACHE_DIR = ROOT / "cache" / f"{AOI_NAME}_zones"       # Sentinel-2 statistics per year and zone (notebook 01)
CLIMATE_DIR = ROOT / "cache" / "climate" / AOI_NAME    # clipped climate data and zone series (notebook 02)
OUT_DIR = ROOT / "results" / AOI_NAME                  # phenology results (notebook 03)
CLIMATE_OUT_DIR = OUT_DIR / "climate"                  # climate analysis results (notebook 04)

# ---------------------------------------------------------------- Sentinel-2 (01) and date filter (03)
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

# Topographic zones: elevation band x north/south facing (+ flat)
DEM_COLLECTION = "cop-dem-glo-30"
ELEV_STEP = 200            # m
FLAT_SLOPE = 5             # degrees
MIN_ZONE_PIXELS = 200

# ---------------------------------------------------------------- phenology metrics (03)
INDICES = ["NDVI", "GRVI", "PSRI"]
SMOOTH_WINDOW = 7          # 5-day steps -> centred 35-day moving average
EOS_FIXED_THRESHOLD = 0.5
MIN_POINTS_PER_YEAR = 30   # valid 5-day values needed for an EOS
FIT_WINDOW = (182, 365)    # DOY range of the logistic autumn fit
MIN_OBS_PER_YEAR = 6       # clear observations in FIT_WINDOW needed for a logistic fit
TRANSITION_FRACTIONS = {"onset": 0.2, "mid": 0.5, "end": 0.8}
EXPECT_DECREASE = {"NDVI": True, "GRVI": True, "PSRI": False}   # PSRI rises with yellowing
MIN_OBS_SIDE = 2           # clear observations needed on each side of the logistic mid point
ALPHA = 0.05
FORECAST_YEARS = 2

# ---------------------------------------------------------------- climate data (02)
# MeteoSwiss gridded observations (1 km, LV95): variable -> product
OBS_GRID_PRODUCTS = {"tas": "tabsd", "tasmin": "tmind", "tasmax": "tmaxd", "pr": "rhiresd", "srel": "sreld"}
CLIMATE_SPINUP_DAYS = 92   # observations also downloaded for the last days of FIRST_YEAR - 1
GRID_BUFFER = 2000         # m around the AOI when clipping grids
LAPSE_RATE_FALLBACK = -0.0065   # K/m, used if the lapse rate cannot be fitted from the grid

# Station for SMN observations and CH2025 DAILY-LOCAL scenarios: Buffalora (1971 m, ~8 km from the AOI)
STATION = "BUF"
STATION_PARAMS = {"tas": "tre200d0", "tasmin": "tre200dn", "tasmax": "tre200dx", "pr": "rre150d0",
                  "rsds": "gre000d0", "hurs": "ure200d0", "sfcwind": "fkl010d0", "et0": "erefaod0"}
TEMPERATURE_VARS = ["tas", "tasmin", "tasmax"]   # shifted to each zone's elevation with the lapse rate

# CH2025 climate scenarios (30-year daily series per global warming level, 26 model chains)
CH2025_PERIODS = ["ref91-20", "gwl1.5", "gwl2.0", "gwl2.5", "gwl3.0"]
CH2025_LOCAL_VARS = ["tas", "tasmin", "tasmax", "pr", "hurs", "sfcwind"]
CH2025_GRID_VARS = ["tas", "tasmin", "tasmax", "pr"]
CH2025_GRID_MODELS = None  # None = all model chains, or a list such as ["clmcom-cclm4-cccma"]

# ---------------------------------------------------------------- climate analysis (04)
# Phenology dates to explain/predict: "<INDEX> <metric>", metric = eos_mid | eos_fixed | onset | mid | end
# (eos_* only for NDVI, from the smoothed curve; onset/mid/end from the logistic fit)
TARGETS = ["NDVI eos_mid", "NDVI mid", "GRVI mid", "PSRI mid", "PSRI onset"]
