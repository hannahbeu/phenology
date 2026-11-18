"""Functions shared by several notebooks."""
import time

import numpy as np
import pandas as pd
import requests
import rioxarray
import xarray as xr
from pyproj import Transformer

from config import (CACHE_DIR, END, GRID_BUFFER, MAX_SCENE_CLOUD, MAX_SCL_FRACTION, MIN_COVERED_PIXELS,
                    MIN_VALID_FRACTION, REPORT_FIG_DIR, SCL_GROUPS, SEASON_COMPLETE_DOY, START, TEMPERATURE_VARS,
                    VALID_SHARE_OF, YEARS)

QUALITY_COLS = ["scene_cloud_cover"] + [f"scl_{g}_fraction" for g in SCL_GROUPS]


# ---------------------------------------------------------------- figures
DATE_TYPE_TITLES = {"start": "Start of the yellowing", "peak": "Peak of the yellowing", "end": "End of the yellowing"}


def date_title(target):
    # Figure title of a date type ("start" -> "Start of the yellowing"); other targets are shown as they are
    return DATE_TYPE_TITLES.get(target, target)


def save_report_figure(fig, name):
    # Saves a figure recommended for the report as REPORT_FIG_DIR/<name>.png (300 dpi); name starts with its
    # number in the report order, e.g. "11_season_dates_chosen"
    REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(REPORT_FIG_DIR / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")


# ---------------------------------------------------------------- Sentinel-2 statistics cache
def cached_years():
    # YEARS up to the current year (no future downloads)
    return [y for y in YEARS if y <= pd.Timestamp.today().year]


def load_stats(cache_dir=CACHE_DIR):
    # Per-date statistics of all zones (long format: one row per date and zone), cropped to START..END.
    # cache_dir: CACHE_DIR (topographic zones) or SITE_CACHE_DIR (areas around local sites)
    missing = [y for y in cached_years() if not (cache_dir / f"stats_{y}.csv").exists()]
    if missing:
        print(f"Not cached yet in {cache_dir.name}: {missing} (run 01_download_sentinel2)")
    frames = [pd.read_csv(cache_dir / f"stats_{y}.csv", index_col="date", parse_dates=["date"])
              for y in cached_years() if y not in missing]
    return pd.concat([f for f in frames if not f.empty]).sort_index(kind="stable").loc[START:END]


def incomplete_years(stats):
    # Years whose cache ends before SEASON_COMPLETE_DOY (downloaded while the autumn was still in progress)
    last = stats.index.to_series().groupby(stats.index.year).max()
    return [int(year) for year, day in last.items() if day.dayofyear < SEASON_COMPLETE_DOY]


def last_complete_season():
    # Latest year whose autumn is over by today (SEASON_COMPLETE_DOY reached)
    today = pd.Timestamp.today()
    return today.year if today.dayofyear >= SEASON_COMPLETE_DOY else today.year - 1


def load_zone_table(cache_dir=CACHE_DIR):
    return pd.read_csv(cache_dir / "zones.csv", index_col="zone")


def index_frame(stats, name, zone="all", zone_table=None):
    # Statistics of one index (lower-case name, e.g. "ndvi") and zone, with the date quality columns.
    # valid_fraction and the scl_* shares (except nodata) refer to VALID_SHARE_OF; zone_valid_fraction is always the
    # clear share of all zone pixels, covered_fraction / covered_pixels the part of the zone inside the scene.
    # zone_table: the zone table of the cache stats comes from (default: load_zone_table())
    cols = [f"{name}_mean", f"{name}_median", f"{name}_std", f"{name}_valid_fraction"]
    frame = stats.loc[stats.zone == zone, cols + QUALITY_COLS].rename(
        columns={f"{name}_valid_fraction": "zone_valid_fraction"})
    frame.insert(3, "valid_fraction", frame.zone_valid_fraction)
    covered = 1 - frame.scl_nodata_fraction
    frame["covered_fraction"] = covered
    frame["zone_pixels"] = (load_zone_table() if zone_table is None else zone_table).n_pixels[zone]
    frame["covered_pixels"] = (covered * frame.zone_pixels).round().astype(int)
    if VALID_SHARE_OF == "covered":
        shares = ["valid_fraction"] + [f"scl_{g}_fraction" for g in SCL_GROUPS if g != "nodata"]
        frame[shares] = frame[shares].div(covered.where(covered > 0), axis=0)
    elif VALID_SHARE_OF != "zone":
        raise ValueError(f"VALID_SHARE_OF must be 'covered' or 'zone', not {VALID_SHARE_OF!r}")
    return frame


def quality_ok(frame):
    # Date filter on tile cloud cover, scene footprint and SCL shares, shared by all indices. The scene must cover
    # MIN_COVERED_PIXELS of the zone, or the whole zone if it is smaller
    ok = ((frame.scene_cloud_cover <= MAX_SCENE_CLOUD)
          & (frame.covered_pixels >= np.minimum(MIN_COVERED_PIXELS, frame.zone_pixels)))
    for group, limit in MAX_SCL_FRACTION.items():
        ok &= frame[f"scl_{group}_fraction"] <= limit
    return ok


def clean_frame(stats, name, zone="all", zone_table=None):
    frame = index_frame(stats, name, zone, zone_table)
    return frame[quality_ok(frame) & (frame.valid_fraction >= MIN_VALID_FRACTION)].copy()


# ---------------------------------------------------------------- MeteoSwiss open data (STAC)
STAC_URL = "https://data.geo.admin.ch/api/stac/v1/collections/"


def stac_get(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def stac_items(collection):
    url, items = f"{STAC_URL}{collection}/items?limit=100", []
    while url:
        page = stac_get(url)
        items += page["features"]
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
    return items


def collection_asset(collection, name):
    return stac_get(f"{STAC_URL}{collection}")["assets"][name]["href"]


def download(url, path, retries=4):
    # Streamed download to path (via a .part file, so an interrupted download never looks complete)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(part, "wb") as f:
                    for chunk in r.iter_content(2 ** 22):
                        f.write(chunk)
            part.replace(path)
            return path
        except (requests.RequestException, OSError):
            if attempt == retries - 1:
                raise
            time.sleep(30 * (attempt + 1))


# ---------------------------------------------------------------- zones on the 1 km climate grid
def zone_cells():
    # Zone pixels of zones.tif aggregated to the 1 km LV95 cells of the MeteoSwiss grids.
    # weights: one row per zone and cell (pixel share, mean elevation of the zone pixels in the cell)
    # cells: elevation of every cell covered by zones.tif (mean of all its pixels, used for the lapse rate)
    zr = rioxarray.open_rasterio(CACHE_DIR / "zones.tif", masked=True)
    elev, elev_band, zone_id = (zr.sel(band=b).values.ravel() for b in (1, 2, 4))
    yy, xx = np.meshgrid(zr.y.values, zr.x.values, indexing="ij")
    east, north = Transformer.from_crs(zr.rio.crs, "EPSG:2056", always_xy=True).transform(xx.ravel(), yy.ravel())
    pix = pd.DataFrame({"E": np.floor(east / 1000) * 1000 + 500, "N": np.floor(north / 1000) * 1000 + 500,
                        "elev": elev, "zone_id": zone_id, "in_aoi": ~np.isnan(elev_band)}).dropna(subset=["elev"])
    cells = pix.groupby(["E", "N"]).elev.mean().rename("cell_elev")

    names = load_zone_table().index
    groups = [("all", pix[pix.in_aoi])] + [(names[int(i)], g) for i, g in pix.dropna(subset=["zone_id"])
                                          .groupby("zone_id")]
    parts = []
    for zone, g in groups:
        w = g.groupby(["E", "N"]).agg(n=("elev", "size"), zone_elev=("elev", "mean")).reset_index()
        parts.append(w.assign(zone=zone, weight=w.n / w.n.sum()))
    weights = pd.concat(parts, ignore_index=True).join(cells, on=["E", "N"])
    return weights, cells


def grid_bbox(weights):
    return (weights.E.min() - GRID_BUFFER, weights.N.min() - GRID_BUFFER,
            weights.E.max() + GRID_BUFFER, weights.N.max() + GRID_BUFFER)


def clip_grid(ds, bbox):
    e0, n0, e1, n1 = bbox
    return ds.sel(E=slice(e0, e1), N=slice(n0, n1))


def grid_extent(ds):
    return float(ds.E.min()), float(ds.N.min()), float(ds.E.max()), float(ds.N.max())


def covers(ds, bbox):
    # True if the clipped grid ds contains every cell of bbox
    e0, n0, e1, n1 = grid_extent(ds)
    return e0 <= bbox[0] and n0 <= bbox[1] and e1 >= bbox[2] and n1 >= bbox[3]


def fetch_bbox(path, bbox):
    # Box to clip a (re)download of a shared source file to: None if the cached file already covers bbox, else
    # bbox joined with the cached extent, so the file stays valid for the AOIs that used it before
    if not path.exists():
        return bbox
    with xr.open_dataset(path) as ds:
        if covers(ds, bbox):
            return None
        old = grid_extent(ds)
    return min(old[0], bbox[0]), min(old[1], bbox[1]), max(old[2], bbox[2]), max(old[3], bbox[3])


def add_calendar(ds):
    # year / month / doy coordinates for real (datetime) and model (cftime, 365-day) calendars. doy is counted
    # in a 365-day year (29 Feb shares doy 60 with 1 Mar), so windows mean the same dates in both.
    t = ds.indexes["time"]
    month, day = np.asarray(t.month), np.asarray(t.day)
    doy = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])[month - 1] + day
    return ds.assign_coords(year=("time", np.asarray(t.year)), month=("time", month), doy=("time", doy))


def fit_lapse_rates(temps, cells):
    # Monthly lapse rate (K/m) per temperature variable: slope of the cells' mean temperature against elevation
    sel = {"E": xr.DataArray(cells.index.get_level_values("E").values, dims="cell"),
           "N": xr.DataArray(cells.index.get_level_values("N").values, dims="cell")}
    rates = {}
    for var in TEMPERATURE_VARS:
        clim = temps[var].groupby("time.month").mean().sel(**sel)
        rates[var] = []
        for m in range(1, 13):
            t = clim.sel(month=m).values
            ok = np.isfinite(t)   # cells outside the grid domain are NaN
            rates[var].append(np.polyfit(cells.values[ok], t[ok], 1)[0])
    return pd.DataFrame(rates, index=pd.Index(range(1, 13), name="month"))


def grid_to_zones(ds, weights, lapse):
    # Weighted mean of every gridded variable over each zone's cells -> new dimension "zone". Temperatures are
    # shifted from each cell's elevation to the mean elevation of the zone pixels in that cell.
    cells = weights[["E", "N"]].drop_duplicates().reset_index(drop=True)
    zones = list(dict.fromkeys(weights.zone))
    w = (weights.merge(cells.reset_index(), on=["E", "N"])
         .pivot_table(index="index", columns="zone", values="weight", fill_value=0)[zones])
    w = xr.DataArray(w.values, dims=("cell", "zone"), coords={"zone": zones})
    offset = (weights.weight * (weights.zone_elev - weights.cell_elev)).groupby(weights.zone).sum()
    offset = xr.DataArray(offset[zones].values, dims="zone", coords={"zone": zones})
    at_cells = ds.sel(E=xr.DataArray(cells.E.values, dims="cell"), N=xr.DataArray(cells.N.values, dims="cell"))
    out = xr.Dataset({var: at_cells[var].dot(w, dim="cell") for var in ds.data_vars})
    for var in TEMPERATURE_VARS:
        if var in out:
            out[var] = out[var] + lapse_by_month(lapse[var], out) * offset
    return out


def lapse_by_month(rate, ds):
    return xr.DataArray(rate.reindex(ds.month.values).values, dims="time", coords={"time": ds.time})
