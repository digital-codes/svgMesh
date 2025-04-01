import os
import requests
import mercantile
from pyproj import Transformer
from osgeo import ogr, osr
import re


# Coordinate conversion helper
def local_to_global(x_local, y_local,tile_bounds,extent):
    x0, y0, x1, y1 = tile_bounds.left, tile_bounds.bottom, tile_bounds.right, tile_bounds.top
    scale_x = (x1 - x0) / extent
    scale_y = (y1 - y0) / extent

    x_world = x0 + x_local * scale_x
    y_world = y0 + y_local * scale_y  # ✅ No Y flip!

    return x_world, y_world

# Transform geometry manually
def transform_geometry_to_3857(geom,tile_bounds,extent):
    geom_type = geom.GetGeometryType()
    geom_name = geom.GetGeometryName().upper()
    geom_out = ogr.Geometry(geom_type)

    if geom_name == 'POINT':
        x_local, y_local, *_ = geom.GetPoint()
        x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
        pt = ogr.Geometry(ogr.wkbPoint)
        pt.AddPoint(x_world, y_world)
        return pt

    elif geom_name == 'MULTIPOINT':
        mp = ogr.Geometry(ogr.wkbMultiPoint)
        for i in range(geom.GetGeometryCount()):
            pt = geom.GetGeometryRef(i)
            x_local, y_local, *_ = pt.GetPoint()
            x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
            pt_out = ogr.Geometry(ogr.wkbPoint)
            pt_out.AddPoint(x_world, y_world)
            mp.AddGeometry(pt_out)
        return mp

    elif geom_name == 'LINESTRING':
        line_out = ogr.Geometry(ogr.wkbLineString)
        for j in range(geom.GetPointCount()):
            x_local, y_local, *_ = geom.GetPoint(j)
            x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
            line_out.AddPoint(x_world, y_world)
        return line_out

    elif geom_name == 'MULTILINESTRING':
        multi = ogr.Geometry(ogr.wkbMultiLineString)
        for i in range(geom.GetGeometryCount()):
            line = geom.GetGeometryRef(i)
            line_out = ogr.Geometry(ogr.wkbLineString)
            for j in range(line.GetPointCount()):
                x_local, y_local, *_ = line.GetPoint(j)
                x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
                line_out.AddPoint(x_world, y_world)
            multi.AddGeometry(line_out)
        return multi

    elif geom_name == 'POLYGON':
        poly = ogr.Geometry(ogr.wkbPolygon)
        for i in range(geom.GetGeometryCount()):
            ring = geom.GetGeometryRef(i)
            ring_out = ogr.Geometry(ogr.wkbLinearRing)
            for j in range(ring.GetPointCount()):
                x_local, y_local, *_ = ring.GetPoint(j)
                x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
                ring_out.AddPoint(x_world, y_world)
            if ring_out.GetPointCount() >= 4:
                poly.AddGeometry(ring_out)
        return poly if poly.GetGeometryCount() > 0 else None

    elif geom_name == 'MULTIPOLYGON':
        multi = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in range(geom.GetGeometryCount()):
            poly = geom.GetGeometryRef(i)
            poly_out = ogr.Geometry(ogr.wkbPolygon)
            for j in range(poly.GetGeometryCount()):
                ring = poly.GetGeometryRef(j)
                ring_out = ogr.Geometry(ogr.wkbLinearRing)
                for k in range(ring.GetPointCount()):
                    x_local, y_local, *_ = ring.GetPoint(k)
                    x_world, y_world = local_to_global(x_local, y_local,tile_bounds,extent)
                    ring_out.AddPoint(x_world, y_world)
                if ring_out.GetPointCount() >= 4:
                    poly_out.AddGeometry(ring_out)
            if poly_out.GetGeometryCount() > 0:
                multi.AddGeometry(poly_out)
        return multi if multi.GetGeometryCount() > 0 else None

    else:
        print(f"⚠️ Unsupported geometry type: {geom_name}")
        return None

# --- Configuration ---
center_lat, center_lon = 49.006889, 8.403653
radius_m = 3000  # in meters
zoom = 15
tile_url_template = "https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/tiles/v2/bm_web_de_3857/{z}/{x}/{y}.pbf"
keywords = ["Verkehr", "Siedlung", "Gebaeude", "Gebäude", "Bauwerk", "Gewaesser", "Adresse", "Name_"]

# --- Prepare Output ---
os.makedirs("geojson_tiles", exist_ok=True)

# --- Transform center to EPSG:3857 ---
to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x_center, y_center = to_3857.transform(center_lon, center_lat)

x_min = x_center - radius_m
x_max = x_center + radius_m
y_min = y_center - radius_m
y_max = y_center + radius_m

# --- Convert bounds back to lat/lon for tile selection ---
to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
lon_min, lat_min = to_4326.transform(x_min, y_min)
lon_max, lat_max = to_4326.transform(x_max, y_max)

tiles = list(mercantile.tiles(lon_min, lat_min, lon_max, lat_max, zoom))
print(f"🔍 Selected {len(tiles)} tiles at zoom {zoom}")

# --- Initialize collector ---
merged_layer_dict = {}

# --- Download and process each tile ---
for tile in tiles:
    x, y, z = tile.x, tile.y, tile.z
    url = tile_url_template.format(z=z, x=x, y=y)
    tile_filename = f"geojson_tiles/tile_{z}_{x}_{y}.pbf"


    # Assume this is inside the tile loop:
    tile_bounds = mercantile.xy_bounds(x, y, z)
    print("Bounds:",tile_bounds)
    extent = 4096.0  # MVT default

    # Download tile
    # Check if the file already exists
    if not os.path.exists(tile_filename):
        print(f"⬇️ Downloading {tile_filename}")
        r = requests.get(url)
        if r.status_code == 200:
            with open(tile_filename, "wb") as f:
                f.write(r.content)
        else:
            print(f"❌ Failed to download tile: {url}")
            continue
    else:  # If the file exists, skip downloading
        print(f"✅ Tile already exists: {tile_filename}")   

    # Open tile with GDAL
    ds = ogr.Open(f"MVT:{tile_filename}")
    if not ds:
        print(f"⚠️ Could not open tile: {tile_filename}")
        continue

    for i in range(ds.GetLayerCount()):
        layer = ds.GetLayer(i)
        lname = layer.GetName()

        if not any(re.search(k, lname, re.IGNORECASE) for k in keywords):
            continue

        if lname not in merged_layer_dict:
            merged_layer_dict[lname] = []

        for feat in layer:
            geom = feat.GetGeometryRef()
            if geom:
                try:
                    if not geom.IsValid():
                        geom = geom.Buffer(0)  # Try to fix

                    transformed_geom = transform_geometry_to_3857(geom,tile_bounds,extent)

                    if transformed_geom and transformed_geom.IsValid():
                        merged_layer_dict[lname].append(
                            {
                                "properties": {k: feat.GetField(k) for k in feat.keys()},
                                "geometry":transformed_geom
                            }
                        )
                    else:
                        print(f"⚠️ Invalid geometry in {tile_filename}, layer: {lname}")
                except Exception as e:
                    print(f"❌ Error reading geometry in {tile_filename}, layer: {lname} → {e}")

# --- Output GeoJSONs (EPSG:3857) ---
driver = ogr.GetDriverByName("GeoJSON")
srs = osr.SpatialReference()
srs.ImportFromEPSG(3857)

for lname, features in merged_layer_dict.items():
    print(f"🛠️ Writing {lname} with {len(features)} features...")
    output_ds = driver.CreateDataSource(f"{lname}_merged.geojson")
    layer = output_ds.CreateLayer(lname, srs, ogr.wkbUnknown)

    # Build complete field schema from all features
    all_keys = set()
    for feat in features:
        all_keys.update(feat["properties"].keys())

    for key in all_keys:
        # Guess field type from first non-None value
        sample_value = next((f["properties"].get(key) for f in features if f["properties"].get(key) is not None), "")
        if isinstance(sample_value, int):
            field_type = ogr.OFTInteger
        elif isinstance(sample_value, float):
            field_type = ogr.OFTReal
        else:
            field_type = ogr.OFTString
        field = ogr.FieldDefn(key, field_type)
        layer.CreateField(field)

    for feature in features:
        geom = feature["geometry"]
        props = feature["properties"]
        try:
            if not geom.IsValid():
                geom = geom.Buffer(0)

            if geom.IsValid():
                feat = ogr.Feature(layer.GetLayerDefn())
                feat.SetGeometry(geom)

                # Set all attribute fields
                for key, value in props.items():
                    if value is not None:
                        feat.SetField(key, value)

                layer.CreateFeature(feat)
                feat = None
        except Exception as e:
            print(f"❌ Geometry write error: {e}")

    output_ds = None
    print(f"✅ Saved {lname}_merged.geojson")
