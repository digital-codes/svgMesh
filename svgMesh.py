import numpy as np
import trimesh
from svgpathtools import svg2paths2
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
import xml.etree.ElementTree as ET


def parse_svg_polygons(svg_file, scale=1.0):
    tree = ET.parse(svg_file)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    polygons = []
    for elem in root.iter():
        if elem.tag.endswith('polygon'):
            points_str = elem.attrib.get('points', '')
            points = []
            for point in points_str.strip().split():
                try:
                    x, y = map(float, point.strip().split(','))
                    points.append((x * scale, y * scale))
                except:
                    continue
            if len(points) >= 3:
                poly = Polygon(points)
                if poly.is_valid:
                    polygons.append(poly)
    return polygons


def svg_path_to_polygons(svg_paths, scale=1.0):
    from svgpathtools import Path
    polygons = []
    for path in svg_paths:
        if isinstance(path, Path):
            points = [(seg.start.real * scale, seg.start.imag * scale) for seg in path]
            if len(points) > 2:
                poly = Polygon(points)
                if poly.is_valid:
                    polygons.append(poly)
    return polygons


def extrude_svg(svg_file, extrusion_height=5.0, scale=1.0, output_file="output.glb"):
    # Parse path and polygon elements
    paths, _, _ = svg2paths2(svg_file)
    path_polys = svg_path_to_polygons(paths, scale)
    polygon_elements = parse_svg_polygons(svg_file, scale)

    all_polygons = path_polys + polygon_elements
    if not all_polygons:
        raise ValueError("No valid shapes to extrude.")

    # Combine all valid geometry
    combined = unary_union(all_polygons)

    # Handle MultiPolygon or single Polygon
    meshes = []
    if isinstance(combined, MultiPolygon):
        for poly in combined.geoms:
            mesh = extrude_polygon(poly, height=extrusion_height)
            meshes.append(mesh)
    elif isinstance(combined, Polygon):
        mesh = extrude_polygon(combined, height=extrusion_height)
        meshes.append(mesh)
    else:
        raise TypeError("Unsupported geometry type.")

    # Combine into a single mesh
    final_mesh = trimesh.util.concatenate(meshes)
    final_mesh.export(output_file)
    print(f"✅ Exported: {output_file}")


# Example usage
extrude_svg("example.svg", extrusion_height=10.0, scale=0.1, output_file="extruded_model.glb")
