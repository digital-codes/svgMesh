# Re-running the code after environment reset to restore the script functionality.

import argparse
import os
import numpy as np
import random
import trimesh
from PIL import Image
import xml.etree.ElementTree as ET
from svgpathtools import svg2paths2
from svgpathtools import Path
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import scale
from trimesh.creation import extrude_polygon


def parse_svg_polygons(svg_file, scale=1.0, auto_close=False):
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
                    points.append((x * scale, -y * scale))
                except:
                    continue
            if auto_close:
                poly = close_polygon(points)
            else:
                poly = Polygon(points)
            if poly and poly.is_valid:
                polygons.append(poly)
    return polygons


def svg_path_to_polygons(svg_paths, scale=1.0, auto_close=False, min_points=3):
    polygons = []

    for path in svg_paths:
        if isinstance(path, Path):
            # Sample points along the path (curve)
            sampled = [path.point(t) for t in np.linspace(0, 1, num=50)]
            points = [(p.real * scale, -p.imag * scale) for p in sampled]

            if auto_close and len(points) >= 2:
                if points[0] != points[-1]:
                    points.append(points[0])

            if len(points) >= min_points:
                poly = Polygon(points)
                if poly.is_valid and not poly.is_empty:
                    polygons.append(poly)
    return polygons


def close_polygon(points):
    if len(points) < 3:
        return None
    # If not already closed, append the first point to the end
    if points[0] != points[-1]:
        points.append(points[0])
    return Polygon(points)


def simplify_polygon(polygon, tolerance=0.5):
    return polygon.simplify(tolerance, preserve_topology=True)


def normalize_polygons(polygons, max_size=100.0):
    combined = MultiPolygon(polygons)
    minx, miny, maxx, maxy = combined.bounds
    width = maxx - minx
    height = maxy - miny
    current_max = max(width, height)
    if current_max <= max_size:
        return polygons
    scale_factor = max_size / current_max
    scaled = [scale(p, xfact=scale_factor, yfact=scale_factor, origin=(0, 0)) for p in polygons]
    return scaled


def apply_texture(mesh, image_path, tile_scale=10):
    image = Image.open(image_path).convert("RGBA")
    uv = mesh.vertices[:, :2] * tile_scale
    uv = uv - uv.min(axis=0)
    uv = uv / uv.max(axis=0)
    mesh.visual = trimesh.visual.texture.TextureVisuals(uv=uv, image=image)
    return mesh


def extrude_svg_with_textures(
    svg_file,
    extrusion_height=5.0,
    scale=1.0,
    tolerance=0.5,
    max_size=100.0,
    tile_scale=10,
    auto_close=False
):
    paths, _, _ = svg2paths2(svg_file)
    path_polys = svg_path_to_polygons(paths, scale, auto_close)
    polygon_elements = parse_svg_polygons(svg_file, scale, auto_close)
    raw_polygons = path_polys + polygon_elements

    simplified_polygons = []
    for poly in raw_polygons:
        simplified = simplify_polygon(poly, tolerance=tolerance) if tolerance > 0 else poly
        if simplified.is_valid and not simplified.is_empty:
            simplified_polygons.append(simplified)

    all_polygons = normalize_polygons(simplified_polygons, max_size=max_size)

    textures = ["hatch1.png", "hatch2.png", "hatch3.png", "hatch4.png"]
    meshes = []

    for idx, poly in enumerate(all_polygons):
        poly = unary_union(poly)
        if isinstance(poly, Polygon):
            mesh = extrude_polygon(poly, height=extrusion_height)
            texture_path = random.choice(textures)
            mesh = apply_texture(mesh, texture_path, tile_scale=tile_scale)
            mesh.apply_translation([0, 0, -extrusion_height / 2])  # center vertically
            meshes.append(mesh)

    combined = trimesh.util.concatenate(meshes)
    combined.remove_unreferenced_vertices()
    
    # Shift to bottom-center of bounding box
    bbox = combined.bounds
    center_xy = (bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2
    combined.apply_translation([-center_xy[0], -center_xy[1], -bbox[0][2]])

    return combined

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrude SVG paths to 3D mesh")
    parser.add_argument("-i", "--input", type=str, help="Input SVG file", default="example.svg")
    parser.add_argument("-o", "--output", type=str, default="model.glb", help="Output GLB/GLTF file")
    parser.add_argument("-e", "--extrusion", type=float, default=1.0, help="Extrusion height")
    parser.add_argument("-s", "--scale", type=float, default=1.0, help="Scale factor")
    parser.add_argument("-t", "--tolerance", type=float, default=0.8, help="Simplify tolerance")
    parser.add_argument("-m", "--max_size", type=float, default=10.0, help="Max size")
    parser.add_argument("--tile_scale", type=float, default=10, help="Texture tile scale")
    parser.add_argument("--auto_close", action="store_true", help="Auto-close open paths or polygons.")
    args = parser.parse_args()
    
    mesh = extrude_svg_with_textures(
        svg_file=args.input,
        extrusion_height=args.extrusion,
        scale=args.scale,
        tolerance=args.tolerance,
        max_size=args.max_size,
        tile_scale=args.tile_scale,
        auto_close=args.auto_close
    )

    if mesh:
        
        # Choose export type based on extension
        file_type = os.path.splitext(args.output)[-1].lower()

        if file_type == '.glb':
            mesh.export(args.output, file_type='glb')
            if not os.path.exists("viewer/public"):
                os.makedirs("viewer/public")
            mesh.export("viewer/public/preview.glb", file_type='glb')  # save preview.glb for web viewer
        elif file_type == '.gltf':
            mesh.export(args.output, file_type='gltf')  # saves .gltf + .bin + textures if present
        else:
            raise ValueError("Output file must end in .glb or .gltf")

        print(f"\n✅ Exported: {args.output}")
        print(f"🔢 Vertices: {len(mesh.vertices)}")
        print(f"🔺 Faces: {len(mesh.faces)}")
        print(f"📦 Bounding Box: {mesh.bounds}")
            
    else:
        print("❌ No mesh generated.")
        
