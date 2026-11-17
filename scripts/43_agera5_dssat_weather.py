#!/usr/bin/env python
"""
43_agera5_dssat_weather.py

AgERA5 v2.0 daily weather for the 27 cross-state counties, written as one DSSAT XML
weather file (<WDB><Stations ...><Weather Columns="Year,DOY,SRAD,Tmax,Tmin,Rain,WindSp,SH,Rmax,Rmin">)
per county.

Usage
-----

python 43_agera5_dssat_weather.py --probe                       # one-day test request first
python 43_agera5_dssat_weather.py --archive --years $(seq 1986 2024) [--items aquacrop|dssat|all]
        [--states IL IN IA MI MN MO OH SD WI]   # daily grids -> shared_inputs/agera5_archive/<tag>/<tag>_<year>.nc
python 43_agera5_dssat_weather.py [--years 2015] [--mode centroid|mean]
        [--header-from EXISTING.xml] [--elev-csv FILE] [--tav-amp] [--sites SITE ...]

Station
    centroid (default): the native 0.1 deg AgERA5 cell nearest the county centroid;
                        Lat/Long = that cell's centre.
    mean:               mean over native cells whose centres lie inside the county;
                        Lat/Long = county centroid.
Download
    One CDS request per variable per year over a box covering all counties, sent one at a
    time (CDS rejects parallel queued requests; on "queue full" the script waits and retries).
    If CDS refuses the 'area' key, it falls back to global daily files and keeps only the
    station cells; each request is extracted and deleted before the next.
    Extracted series are cached in results/dssat_weather/cache/, so a rerun skips finished requests.

Variables and conversions (AgERA5 -> DSSAT column)
    solar_radiation_flux (J m-2 d-1)            -> SRAD   MJ m-2 d-1 (/1e6)
    2m_temperature 24_hour_maximum/minimum (K)  -> Tmax, Tmin  degC
    precipitation_flux (mm d-1)                 -> Rain   mm
    10m_wind_speed 24_hour_mean (m s-1)         -> WindSp m s-1 at 2 m (x 4.87/ln(67.8*10-5.42), FAO-56 eq. 47)
    vapour_pressure 24_hour_mean (hPa)          -> SH     g kg-1, q = 622 e / (p - 0.378 e),
                                                   p from elevation (FAO-56 eq. 7)
    2m_relative_humidity at 06,09,12,15,18 h (%) -> Rmax, Rmin = max, min of the five (approximation)
Elevation: USGS EPQS point query at the station (or --elev-csv site_id,elev_m). If unavailable, Elev
is left blank and p = 1013.25 hPa is used for SH (warned).
Tav, Amp: blank by default, as in your template; --tav-amp fills Tav = mean daily mean temperature and
Amp = warmest minus coldest monthly mean over the years written.
CDS token: CDS_API_TOKEN or first line of ~/.cds_api_token (never printed).
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG = ROOT / "config"
DATASET = "sis-agrometeorological-indicators"
CDS_URL = "https://cds.climate.copernicus.eu/api"
ITEMS = [
    ("tmax", "2m_temperature", {"statistic": ["24_hour_maximum"]}),
    ("tmin", "2m_temperature", {"statistic": ["24_hour_minimum"]}),
    ("rain", "precipitation_flux", {}),
    ("srad", "solar_radiation_flux", {}),
    ("wind10", "10m_wind_speed", {"statistic": ["24_hour_mean"]}),
    ("vp", "vapour_pressure", {"statistic": ["24_hour_mean"]}),
] + [(f"rh{h}", "2m_relative_humidity", {"time": [f"{h}_00"]}) for h in ("06", "09", "12", "15", "18")]
ET0_ITEM = ("et0", "reference_evapotranspiration", {})
ITEM_SETS = {"aquacrop": ["tmax", "tmin", "rain", "et0"],
             "dssat": [i[0] for i in ITEMS],
             "all": [i[0] for i in ITEMS] + ["et0"]}
STATE_FIPS = {"IL": "17", "IN": "18", "IA": "19", "MI": "26", "MN": "27", "MO": "29", "OH": "39",
              "SD": "46", "WI": "55", "NE": "31", "KS": "20"}
WIND_2M = 4.87 / np.log(67.8 * 10 - 5.42)          # 0.748
COLUMNS = "Year,DOY,SRAD,Tmax,Tmin,Rain,WindSp,SH,Rmax,Rmin"


# ---------------------------------------------------------------- stations
def load_stations(site_filter=None):
    import geopandas as gpd
    sites = pd.read_csv(CONFIG / "crossstate_sites.csv", dtype={"fips": str})
    sites["fips"] = sites["fips"].str.zfill(5)
    if site_filter:
        sites = sites[sites.site_id.isin(site_filter)]
    out = []
    for r in sites.itertuples():
        hits = sorted((ROOT / "locations").glob(f"*{r.fips}*/**/*.geojson"))
        if len(hits) != 1:
            sys.exit(f"{r.site_id}: expected one county .geojson under locations/*{r.fips}*/, found {len(hits)}")
        g = gpd.read_file(hits[0]).to_crs(4326)
        poly = g.geometry.union_all() if hasattr(g.geometry, "union_all") else g.geometry.unary_union
        c = gpd.GeoSeries([poly], crs=4326).to_crs(5070).centroid.to_crs(4326).iloc[0]
        out.append(dict(site_id=r.site_id, state=r.state, county=r.county, poly=poly, clat=c.y, clon=c.x))
    return out


def area_box(stations, pad=0.3):
    b = np.array([s["poly"].bounds for s in stations])        # minx, miny, maxx, maxy
    return [round(b[:, 3].max() + pad, 1), round(b[:, 0].min() - pad, 1),
            round(b[:, 1].min() - pad, 1), round(b[:, 2].max() + pad, 1)]   # N, W, S, E


def build_index(lat, lon, stations, mode):
    import shapely
    idx = {}
    for s in stations:
        if mode == "centroid":
            iy, ix = int(np.abs(lat - s["clat"]).argmin()), int(np.abs(lon - s["clon"]).argmin())
            idx[s["site_id"]] = (np.array([iy]), np.array([ix]))
            s["lat"], s["lon"] = float(lat[iy]), float(lon[ix])
        else:
            sub_y = np.where((lat >= s["poly"].bounds[1] - 0.1) & (lat <= s["poly"].bounds[3] + 0.1))[0]
            sub_x = np.where((lon >= s["poly"].bounds[0] - 0.1) & (lon <= s["poly"].bounds[2] + 0.1))[0]
            YY, XX = np.meshgrid(sub_y, sub_x, indexing="ij")
            inside = shapely.contains_xy(s["poly"], lon[XX], lat[YY])
            if not inside.any():
                sys.exit(f"{s['site_id']}: no native AgERA5 cell centre inside the county")
            idx[s["site_id"]] = (YY[inside], XX[inside])
            s["lat"], s["lon"] = s["clat"], s["clon"]
            s["n_cells"] = int(inside.sum())
    return idx


# ---------------------------------------------------------------- download + extract
def token():
    t = os.environ.get("CDS_API_TOKEN", "").strip()
    f = Path.home() / ".cds_api_token"
    if not t and f.exists():
        t = f.read_text().splitlines()[0].strip()
    if not t:
        sys.exit("No CDS token (CDS_API_TOKEN or ~/.cds_api_token).")
    return t


def make_client():
    from ecmwf.datastores import Client
    return Client(url=CDS_URL, key=token())


def request_for(item, year, days=None):
    tag, var, extra = item
    req = {"variable": var, "year": [str(year)], "version": "2_0",
           "month": [f"{m:02d}" for m in range(1, 13)], "day": [f"{d:02d}" for d in range(1, 32)], **extra}
    if days:  # probe
        req["month"], req["day"] = ["01"], days
    return req


def retrieve(client, req, target):
    for _ in range(48):
        try:
            client.retrieve(DATASET, req, str(target))
            return
        except Exception as e:
            if re.search(r"queued requests|queue", str(e), re.I):
                print("  CDS queue full; waiting 5 min ...", flush=True)
                time.sleep(300)
                continue
            raise
    raise RuntimeError("CDS queue stayed full for 4 h")


def nc_files(path, tmp):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        return sorted(Path(tmp).rglob("*.nc"))
    return [Path(path)]


def coord_names(da):
    latn = next(c for c in da.dims if c.lower().startswith("lat"))
    lonn = next(c for c in da.dims if c.lower().startswith("lon"))
    return latn, lonn


def extract(files, idx_holder, stations, mode):
    rows = []
    for f in files:
        with xr.open_dataset(f) as ds:
            v = [k for k in ds.data_vars if k.lower() not in ("crs", "spatial_ref")][0]
            da = ds[v]
            latn, lonn = coord_names(da)
            da = da.transpose(..., latn, lonn)
            if idx_holder.get("idx") is None:
                idx_holder["idx"] = build_index(da[latn].values, da[lonn].values, stations, mode)
            idx = idx_holder["idx"]
            times = pd.to_datetime(ds["time"].values) if "time" in ds.coords else [None]
            arr = da.values.reshape((-1,) + da.shape[-2:])
            for k, t in enumerate(times):
                if t is None:
                    m = re.search(r"(\d{8})", f.name)
                    t = pd.Timestamp(m.group(1))
                row = {"date": pd.Timestamp(t).normalize()}
                for site, (iy, ix) in idx.items():
                    row[site] = float(np.nanmean(arr[k][iy, ix]))
                rows.append(row)
    return pd.DataFrame(rows).groupby("date").mean().sort_index()


# ---------------------------------------------------------------- DSSAT assembly
def elevation(lat, lon):
    try:
        import requests
        r = requests.get("https://epqs.nationalmap.gov/v1/json",
                         params=dict(x=lon, y=lat, wkid=4326, units="Meters", includeDate="false"), timeout=30)
        return float(r.json()["value"])
    except Exception as e:
        print(f"  elevation lookup failed at {lat:.4f},{lon:.4f}: {e}")
        return np.nan


def station_id(lat, lon):
    return f"{abs(lat):.4f}{'N' if lat >= 0 else 'S'}_{abs(lon):.4f}{'W' if lon < 0 else 'E'}"


def assemble(series, site, elev):
    s = {k: v[site] for k, v in series.items()}
    df = pd.DataFrame(s)
    k2c = lambda x: x - 273.15 if np.nanmedian(x) > 100 else x
    p = 1013.25 * ((293 - 0.0065 * elev) / 293) ** 5.26 if np.isfinite(elev) else 1013.25
    rh = df[[c for c in df.columns if c.startswith("rh")]]
    out = pd.DataFrame({
        "Year": df.index.year, "DOY": df.index.dayofyear,
        "SRAD": df["srad"] / 1e6, "Tmax": k2c(df["tmax"]), "Tmin": k2c(df["tmin"]), "Rain": df["rain"],
        "WindSp": df["wind10"] * WIND_2M, "SH": 622 * df["vp"] / (p - 0.378 * df["vp"]),
        "Rmax": rh.max(axis=1).clip(upper=100), "Rmin": rh.min(axis=1).clip(upper=100)}, index=df.index)
    return out


def write_xml(path, st, w, prefix, suffix, tav_amp):
    tav = amp = ""
    if tav_amp:
        tmean = (w["Tmax"] + w["Tmin"]) / 2
        tav = f"{tmean.mean():.1f}"
        mon = tmean.groupby(tmean.index.month).mean()
        amp = f"{mon.max() - mon.min():.1f}"
    sid = station_id(st["lat"], st["lon"])
    elev = "" if not np.isfinite(st["elev"]) else f"{st['elev']:.2f}"
    head = (f'<Stations Amp="{amp}" Elev="{elev}" Hmht="2" Lat="{st["lat"]:.4f}" Long="{st["lon"]:.4f}" '
            f'Place_Name="{st["county"]} County, {st["state"]}" StationID="{sid}" Station_Name="{sid}" '
            f'Tav="{tav}" Tmht="2" Wmht="2">')
    nan_rows = int(w.isna().any(axis=1).sum())
    lines = []
    for r in w.fillna(-99.0).itertuples():
        lines.append(f"{r.Year},{r.DOY},{r.SRAD:.1f},{r.Tmax:.1f},{r.Tmin:.1f},{r.Rain:.2f},"
                     f"{r.WindSp:.1f},{r.SH:.2f},{r.Rmax:.1f},{r.Rmin:.1f}")
    body = (head + "\n    <Storm_Intensity>\n    </Storm_Intensity>\n    <Hourly_Rainfall>\n    </Hourly_Rainfall>\n"
            f'    <Weather Columns="{COLUMNS}">\n' + "\n".join(lines) + "\n</Weather>\n  </Stations>")
    path.write_text(prefix + body + suffix)
    return sid, nan_rows


def template_parts(sample):
    if not sample:
        return "<WDB>\n  ", "\n</WDB>\n"
    t = Path(sample).read_text()
    i, j = t.find("<Stations"), t.rfind("</Stations>")
    if i < 0 or j < 0:
        sys.exit(f"{sample}: no <Stations ...> ... </Stations> block found")
    return t[:i], t[j + len("</Stations>"):]


# ---------------------------------------------------------------- archive mode
def state_box(shp, states, pad=0.3):
    """[N, W, S, E] around all counties of the given states (TIGER county shapefile), padded."""
    import geopandas as gpd
    g = gpd.read_file(shp)
    g = g[g["STATEFP"].isin([STATE_FIPS[s] for s in states])].to_crs(4326)
    if g.empty:
        sys.exit(f"no counties found for {states} in {shp}")
    minx, miny, maxx, maxy = g.total_bounds
    return [float(round(maxy + pad, 1)), float(round(minx - pad, 1)), float(round(miny - pad, 1)), float(round(maxx + pad, 1))]


def run_archive(client, years, tags, box, adir):
    """One CDS request per variable per year over `box`; daily files merged into
    <adir>/<tag>/<tag>_<year>.nc (native 0.1 deg, AgERA5 variable name and attributes kept).
    Existing complete years are skipped; an incomplete year is an error and is not written."""
    items = {i[0]: i for i in ITEMS + [ET0_ITEM]}
    manifest = adir / "archive_manifest.csv"
    for tag in tags:
        (adir / tag).mkdir(parents=True, exist_ok=True)
        for y in years:
            f = adir / tag / f"{tag}_{y}.nc"
            ndays = 366 if pd.Timestamp(y, 12, 31).dayofyear == 366 else 365
            if f.exists():
                with xr.open_dataset(f) as d:
                    if d.sizes.get("time", 0) == ndays:
                        print(f"{tag} {y}: archived, skip", flush=True)
                        continue
            print(f"{tag} {y}: requesting ...", flush=True)
            req = request_for(items[tag], y)
            req["area"] = box
            with tempfile.TemporaryDirectory(dir=adir) as tmp:
                tgt = Path(tmp) / f"{tag}_{y}.download"
                retrieve(client, req, tgt)
                parts = [xr.open_dataset(p) for p in nc_files(tgt, tmp)]
                ds = xr.concat(parts, dim="time", data_vars="minimal", coords="minimal",
                               compat="override").sortby("time")
                ds = ds.sel(time=~ds.get_index("time").duplicated())
                ds.attrs = dict(parts[0].attrs)
                n = ds.sizes["time"]
                if n != ndays:
                    for p_ in parts: p_.close()
                    raise RuntimeError(f"{tag} {y}: {n} days returned, expected {ndays}; not written")
                v = [k for k in ds.data_vars if k.lower() not in ("crs", "spatial_ref")][0]
                tmpf = f.with_suffix(".nc.part")
                ds.load().to_netcdf(tmpf, encoding={v: {"zlib": True, "complevel": 4}})
                for p_ in parts: p_.close()
                tmpf.replace(f)
                latn, lonn = coord_names(ds[v])
                row = pd.DataFrame([dict(tag=tag, year=y, variable=v, days=n,
                                         lat_min=float(ds[latn].min()), lat_max=float(ds[latn].max()),
                                         lon_min=float(ds[lonn].min()), lon_max=float(ds[lonn].max()),
                                         mb=round(f.stat().st_size / 1e6, 1),
                                         utc=pd.Timestamp.utcnow().isoformat(timespec="seconds"))])
                row.to_csv(manifest, mode="a", header=not manifest.exists(), index=False)
                print(f"{tag} {y}: {n} days, {f.stat().st_size/1e6:.1f} MB", flush=True)


# ---------------------------------------------------------------- main
def main(argv=None, client=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2015])
    ap.add_argument("--mode", choices=["centroid", "mean"], default="centroid")
    ap.add_argument("--sites", nargs="*")
    ap.add_argument("--header-from", default=None, help="an existing DSSAT XML weather file to copy the wrapper from")
    ap.add_argument("--elev-csv", default=None)
    ap.add_argument("--tav-amp", action="store_true")
    ap.add_argument("--probe", action="store_true", help="request one day of Tmax and report; no files written")
    ap.add_argument("--out", default=str(ROOT / "results" / "dssat_weather"))
    ap.add_argument("--archive", action="store_true",
                    help="download daily grids over the states' box into --archive-dir (no station files)")
    ap.add_argument("--items", choices=sorted(ITEM_SETS), default="aquacrop",
                    help="archive mode: aquacrop = tmax, tmin, rain, et0; dssat = the 11 station variables; all")
    ap.add_argument("--states", nargs="+", default=["IL", "IN", "IA", "MI", "MN", "MO", "OH", "SD", "WI"])
    ap.add_argument("--counties-shp", default="/mnt/scratch/olusegu3/ORNL_plots/tl_2020_us_county.shp")
    ap.add_argument("--archive-dir", default=str(ROOT / "shared_inputs" / "agera5_archive"))
    a = ap.parse_args(argv)

    if a.archive:
        adir = Path(a.archive_dir); adir.mkdir(parents=True, exist_ok=True)
        box = state_box(a.counties_shp, a.states)
        print(f"archive box [N, W, S, E] = {box}; items {ITEM_SETS[a.items]}; years {a.years[0]}-{a.years[-1]}")
        run_archive(client or make_client(), a.years, ITEM_SETS[a.items], box, adir)
        print("archive complete")
        return 0

    stations = load_stations(a.sites)
    box = area_box(stations)
    out = Path(a.out); cache = out / "cache"; cache.mkdir(parents=True, exist_ok=True)
    client = client or make_client()

    if a.probe:
        for use_area in (True, False):
            req = request_for(ITEMS[0], a.years[0], days=["01"])
            if use_area:
                req["area"] = box
            with tempfile.TemporaryDirectory(dir=out) as tmp:
                tgt = Path(tmp) / "probe.download"
                try:
                    retrieve(client, req, tgt)
                except Exception as e:
                    print(f"probe with area={use_area}: FAILED ({str(e)[:200]})")
                    continue
                f = nc_files(tgt, tmp)
                with xr.open_dataset(f[0]) as ds:
                    v = [k for k in ds.data_vars if k.lower() not in ("crs", "spatial_ref")][0]
                    print(f"probe with area={use_area}: OK, {tgt.stat().st_size/1e6:.1f} MB, "
                          f"variable {v}, grid {dict(ds[v].sizes)}")
            return 0
        return 1

    use_area = True
    idx_holder = {"idx": None}
    series = {}
    for item in ITEMS:
        tag = item[0]
        parts = []
        for y in a.years:
            cf = cache / f"{tag}_{y}_{a.mode}.csv"
            if cf.exists():
                parts.append(pd.read_csv(cf, index_col=0, parse_dates=True)); continue
            print(f"requesting {tag} {y} ...", flush=True)
            with tempfile.TemporaryDirectory(dir=out) as tmp:
                tgt = Path(tmp) / f"{tag}_{y}.download"
                req = request_for(item, y)
                if use_area:
                    req["area"] = box
                try:
                    retrieve(client, req, tgt)
                except Exception as e:
                    if not use_area:
                        raise
                    print(f"  CDS refused the area subset ({str(e)[:120]}); retrying with global files")
                    use_area = False
                    req.pop("area")
                    retrieve(client, req, tgt)
                df = extract(nc_files(tgt, tmp), idx_holder, stations, a.mode)
            df.to_csv(cf)
            parts.append(df)
        series[tag] = pd.concat(parts).sort_index()

    if idx_holder["idx"] is None:   # everything came from cache: rebuild station coordinates
        f = sorted(cache.glob("*.csv"))
        print("all series from cache")
        for s in stations:
            s.setdefault("lat", s["clat"]); s.setdefault("lon", s["clon"])
        coords = cache / f"stations_{a.mode}.csv"
        if coords.exists():
            c = pd.read_csv(coords).set_index("site_id")
            for s in stations:
                s["lat"], s["lon"] = c.loc[s["site_id"], "lat"], c.loc[s["site_id"], "lon"]
    else:
        pd.DataFrame([dict(site_id=s["site_id"], lat=s["lat"], lon=s["lon"]) for s in stations]) \
            .to_csv(cache / f"stations_{a.mode}.csv", index=False)

    elev_over = {}
    if a.elev_csv:
        e = pd.read_csv(a.elev_csv)
        elev_over = dict(zip(e.site_id, e.elev_m))
    prefix, suffix = template_parts(a.header_from)
    index = []
    for s in stations:
        s["elev"] = float(elev_over.get(s["site_id"], np.nan))
        if not np.isfinite(s["elev"]):
            s["elev"] = elevation(s["lat"], s["lon"])
        w = assemble(series, s["site_id"], s["elev"])
        sid = station_id(s["lat"], s["lon"])
        path = out / f"{s['site_id']}_{sid}.xml"
        sid, nan_rows = write_xml(path, s, w, prefix, suffix, a.tav_amp)
        index.append(dict(site_id=s["site_id"], state=s["state"], county=s["county"], station_id=sid,
                          lat=round(s["lat"], 4), lon=round(s["lon"], 4),
                          elev_m=None if not np.isfinite(s["elev"]) else round(s["elev"], 2),
                          days=len(w), missing_days=nan_rows, n_cells=s.get("n_cells", 1), file=path.name))
        print(f"{s['site_id']}: {path.name}  ({len(w)} days, {nan_rows} with missing values)")
    pd.DataFrame(index).to_csv(out / "dssat_weather_index.csv", index=False)
    print(f"Wrote {len(index)} files and dssat_weather_index.csv to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
