import os
import requests
import mercantile
from osgeo import ogr, osr
import re

# Config
center_lat, center_lon = 49.006889, 8.403653
radius_km = 5
zoom = 14
# tile_url_template = "https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/tiles/web_gry/{z}/{x}/{y}.pbf"
tile_url_template = "https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/tiles/v2/bm_web_de_3857/{z}/{x}/{y}.pbf"
layers_of_interest = ['building', 'transportation']
keywords = ["Verkehr", "Siedlung", "Gebaeude", "Gebäude"]

# Convert km to degrees (approximate)
def km_to_deg(km): return km / 111.0

lat_min = center_lat - km_to_deg(radius_km)
lat_max = center_lat + km_to_deg(radius_km)
lon_min = center_lon - km_to_deg(radius_km)
lon_max = center_lon + km_to_deg(radius_km)

tiles = list(mercantile.tiles(lon_min, lat_min, lon_max, lat_max, zooms=zoom))
print(f"Fetching {len(tiles)} tiles...")

merged_layer_dict = {}

# Ensure output directory
os.makedirs("geojson_tiles", exist_ok=True)

# Fetch + convert each tile
for tile in tiles:
    x, y, z = tile.x, tile.y, tile.z
    url = tile_url_template.format(z=z, x=x, y=y)
    tile_filename = f"geojson_tiles/tile_{z}_{x}_{y}.pbf"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/x-protobuf",
        "Referer": "https://sgx.geodatenzentrum.de/",
    }

    # Download
    print(f"Downloading {url}...")
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        with open(tile_filename, "wb") as f:
            f.write(r.content)
        print("Tile downloaded successfully.")
    else:
        print("Failed:", r.status_code, r.text)

    # Open tile via GDAL
    ds = ogr.Open(f"MVT:{tile_filename}")
    if not ds:
        continue

    for i in range(ds.GetLayerCount()):
        layer = ds.GetLayer(i)
        layer_name = layer.GetName()

        if not any(re.search(k, layer_name, re.IGNORECASE) for k in keywords):
            continue

        features = list(layer)
        if layer_name not in merged_layer_dict:
            merged_layer_dict[layer_name] = []

        for feat in features:
            geom = feat.GetGeometryRef()
            if geom:
                try:
                    # Optionally fix geometry
                    if not geom.IsValid():
                        geom = geom.Buffer(0)  # Attempt fix

                    if geom and geom.IsValid():
                        merged_layer_dict[layer_name].append(geom.Clone())
                    else:
                        print(f"⚠️ Invalid geometry skipped in {tile_filename}, layer: {layer_name}")
                except Exception as e:
                    print(f"❌ Geometry error in {tile_filename}, layer: {layer_name} → {e}")

print("Merging layers...")

# Write merged GeoJSON
driver = ogr.GetDriverByName("GeoJSON")
for lname, geoms in merged_layer_dict.items():
    print(f"Processing {lname}...")

    output_ds = driver.CreateDataSource(f"{lname}_merged.geojson")

    # Correct CRS: Web Mercator (EPSG:3857)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)

    layer = output_ds.CreateLayer(lname, srs, ogr.wkbUnknown)

    for geom in geoms:
        try:
            # Fix geometry if invalid
            if not geom.IsValid():
                geom = geom.Buffer(0)

            if geom.IsValid():
                feat_defn = layer.GetLayerDefn()
                feat = ogr.Feature(feat_defn)
                feat.SetGeometry(geom)
                layer.CreateFeature(feat)
                feat = None
            else:
                print(f"⚠️ Skipped invalid geometry in {lname}")
        except Exception as e:
            print(f"❌ Error in {lname}: {e}")

    output_ds = None
    print(f"✅ Saved {lname}_merged.geojson")
    