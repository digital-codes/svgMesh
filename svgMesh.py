import trimesh
import numpy as np
import random
from svgpathtools import svg2paths2
from shapely.geometry import Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
import xml.etree.ElementTree as ET

from PIL import Image

def simplify_polygon(polygon, tolerance=0.5):
    return polygon.simplify(tolerance, preserve_topology=True)

def parse_svg_polygons(svg_file, scale=1.0):
    tree = ET.parse(svg_file)
    root = tree.getroot()
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


def apply_texture(mesh, image_path, tile_scale=10):
    # Load the actual image using PIL
    image = Image.open(image_path).convert("RGBA")

    # Generate planar UVs and tile them
    uv = mesh.vertices[:, :2] * tile_scale
    uv = uv - uv.min(axis=0)
    uv = uv / uv.max(axis=0)

    mesh.visual = trimesh.visual.texture.TextureVisuals(uv=uv, image=image)
    return mesh



def extrude_svg_with_textures(svg_file, extrusion_height=5.0, scale=1.0, output_file="hatched_model.glb"):
    paths, _, _ = svg2paths2(svg_file)
    path_polys = svg_path_to_polygons(paths, scale)
    polygon_elements = parse_svg_polygons(svg_file, scale)

    raw_polygons = path_polys + polygon_elements

    # Simplify all polygons
    all_polygons = []
    for poly in raw_polygons:
        simplified = simplify_polygon(poly, tolerance=0.1)  # tweak tolerance as needed
        if simplified.is_valid and not simplified.is_empty:
            all_polygons.append(simplified)

    if not all_polygons:
        raise ValueError("No valid shapes to extrude.")

    # List of hatch textures
    textures = ["hatch1.png", "hatch2.png", "hatch3.png", "hatch4.png"]

    meshes = []

    for idx, poly in enumerate(all_polygons):
        poly = unary_union(poly)
        if isinstance(poly, Polygon):
            mesh = extrude_polygon(poly, height=extrusion_height)

            # Randomly assign one of the hatch textures
            texture_path = random.choice(textures)
            mesh = apply_texture(mesh, texture_path, tile_scale=10)

            meshes.append(mesh)

    combined = trimesh.util.concatenate(meshes)
    combined.export(output_file)
    print(f"✅ Exported to {output_file} with 4 randomized hatch textures.")


# Example usage
extrude_svg_with_textures(
    svg_file="example.svg",
    extrusion_height=10,
    scale=0.1,
    output_file="hatched_model.glb"
)
