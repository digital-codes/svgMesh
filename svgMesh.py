import numpy as np
import trimesh
import random
from svgpathtools import svg2paths2
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
import xml.etree.ElementTree as ET


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


def create_material(index, texture_files):
    """
    Creates a material using either a texture or a solid color.
    Alternate between color and texture.
    """
    if index % 2 == 0:
        # Solid color material
        color = [255, 0, 0, 255] if index % 4 == 0 else [0, 0, 255, 255]
        material = trimesh.visual.material.PBRMaterial(
            name=f"ColorMat{index}",
            baseColorFactor=np.array(color) / 255
        )
    else:
        # Texture material
        texture_file = texture_files[index % len(texture_files)]
        material = trimesh.visual.material.PBRMaterial(
            name=f"TexMat{index}",
            baseColorTexture=trimesh.visual.texture.TextureVisuals(image=texture_file)
        )
    print("Material: ",material)
    return material


def extrude_svg_with_materials(svg_file, extrusion_height=5.0, scale=1.0, output_file="textured_model.glb"):
    paths, _, _ = svg2paths2(svg_file)
    path_polys = svg_path_to_polygons(paths, scale)
    polygon_elements = parse_svg_polygons(svg_file, scale)

    all_polygons = path_polys + polygon_elements
    if not all_polygons:
        raise ValueError("No valid shapes to extrude.")

    meshes = []
    texture_files = ["hatch1.png", "hatch2.png"]

    for idx, poly in enumerate(all_polygons):
        geom = unary_union(poly) if isinstance(poly, MultiPolygon) else poly
        if isinstance(geom, MultiPolygon):
            for sub in geom.geoms:
                mesh = extrude_polygon(sub, height=extrusion_height)
                mesh.visual.material = create_material(idx, texture_files)
                meshes.append(mesh)
        else:
            mesh = extrude_polygon(geom, height=extrusion_height)
            mesh.visual.material = create_material(idx, texture_files)
            meshes.append(mesh)

    final_mesh = trimesh.util.concatenate(meshes)
    final_mesh.export(output_file)
    print(f"✅ Exported with materials: {output_file}")


# Example usage
extrude_svg_with_materials(
    svg_file="example.svg",
    extrusion_height=10.0,
    scale=0.1,
    output_file="colored_textured_model.glb"
)
