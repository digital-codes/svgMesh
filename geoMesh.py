import argparse
import json
import os
import trimesh
import numpy as np
from shapely.geometry import shape, Polygon, MultiPolygon

def extrude_feature_geometry(geometry, height, simplify_tolerance=None, use_z=False):
    # Separate out Z if needed
    def extract_xy_and_z(coords):
        if isinstance(coords[0][0], (float, int)):
            xy = [(x, y) for x, y, *_ in coords]
            z = coords[0][2] if len(coords[0]) > 2 else 0.0
            return xy, z
        else:
            return [extract_xy_and_z(ring) for ring in coords]

    base_z = 0.0
    geometry = dict(geometry)  # shallow copy

    if use_z:
        extracted = extract_xy_and_z(geometry['coordinates'])

        def strip_out_xy(e):
            if isinstance(e[0], tuple):  # outer ring
                return e[0]
            else:
                return [strip_out_xy(r) for r in e]

        def extract_first_z(e):
            if isinstance(e[0], tuple):
                return e[1]
            else:
                return extract_first_z(e[0])

        geometry['coordinates'] = strip_out_xy(extracted)
        base_z = extract_first_z(extracted)
    else:
        def strip_z(coords):
            if isinstance(coords[0][0], (float, int)):
                return [(x, y) for x, y, *_ in coords]
            else:
                return [strip_z(ring) for ring in coords]

        geometry['coordinates'] = strip_z(geometry['coordinates'])

    geom = shape(geometry)
    if simplify_tolerance:
        geom = geom.simplify(simplify_tolerance, preserve_topology=True)

    polygons = geom.geoms if isinstance(geom, MultiPolygon) else [geom]

    meshes = []
    for poly in polygons:
        mesh = trimesh.creation.extrude_polygon(poly, height)
        mesh = apply_uv_mapping(mesh)
        mesh.apply_translation((0, 0, base_z))  # Move mesh up if Z base provided
        meshes.append(mesh)

    return trimesh.util.concatenate(meshes)

def apply_uv_mapping(mesh):
    vertices = mesh.vertices[:, :2]
    uvs = (vertices - vertices.min(axis=0)) / (vertices.ptp(axis=0) + 1e-6)
    mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)
    return mesh

def extrude_geojson_features(features, simplify_tolerance=None, use_z=False):
    all_meshes = []
    for feature in features:
        geometry = feature['geometry']
        props = feature['properties']
        height = float(props.get('hoehe', 1.0))
        mesh = extrude_feature_geometry(geometry, height, simplify_tolerance, use_z)
        all_meshes.append(mesh)
    return trimesh.util.concatenate(all_meshes)

def main():
    parser = argparse.ArgumentParser(description="Extrude GeoJSON polygons to 3D with UV mapping.")
    parser.add_argument("input", help="Input GeoJSON file")
    parser.add_argument(
        "-s", "--simplify",
        type=float,
        default=None,
        help="Simplification tolerance (optional)"
    )
    parser.add_argument(
        "-z", "--use-z",
        action="store_true",
        help="Use Z as base height for extrusion"
    )
    args = parser.parse_args()

    input_path = args.input
    simplify_tolerance = args.simplify

    with open(input_path, 'r') as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    extruded = extrude_geojson_features(features, simplify_tolerance)

    # ✅ Print mesh summary
    print(f"Total vertices: {len(extruded.vertices)}")
    print(f"Total faces: {len(extruded.faces)}")

    output_path = os.path.splitext(input_path)[0] + ".glb"
    extruded.export(output_path)
    print(f"Exported to {output_path}")

if __name__ == "__main__":
    main()
