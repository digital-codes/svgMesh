import trimesh
from PIL import Image

# load textures
textures = ["hatch1.png", "hatch2.png", "hatch3.png", "hatch4.png","red.png", "blue.png", "yellow.png"]

def apply_texture(mesh, image_path, tile_scale=10):
    image = Image.open(image_path).convert("RGBA")
    uv = mesh.vertices[:, :2] * tile_scale
    uv = uv - uv.min(axis=0)
    uv = uv / uv.max(axis=0)
    mesh.visual = trimesh.visual.texture.TextureVisuals(uv=uv, image=image)
    return mesh


def create_primitive_meshes():
    # Create individual primitives
    cube = trimesh.creation.box(extents=(20, 20, 20))
    cube2 = trimesh.creation.box(extents=(20, 30, 50))
    sphere = trimesh.creation.icosphere(radius=10, subdivisions=3)
    sphere2 = trimesh.creation.icosphere(radius=10, subdivisions=3)
    cylinder = trimesh.creation.cylinder(radius=6, height=20, sections=32)
    torus = trimesh.creation.torus(major_radius=10, minor_radius=4, major_sections=64)

    # Position them for display
    cube2.apply_translation((-30, 0, 0))
    sphere.apply_translation((30, 0, 0))
    sphere2.apply_translation((-60, 0, 0))
    cylinder.apply_translation((60, 0, 0))
    torus.apply_translation((90, 0, 0))

    cube = apply_texture(cube, textures[0])
    cube2 = apply_texture(cube2, textures[1])
    sphere = apply_texture(sphere, textures[2])
    sphere2 = apply_texture(sphere2, textures[3])
    cylinder = apply_texture(cylinder, textures[4])
    torus = apply_texture(torus, textures[5])

    """Create a non-uniformly scaled sphere (ellipsoid)."""
    sphere2_scale_factors=(1.0, 1.5, 0.75)
    sphere2.apply_scale(sphere2_scale_factors)
    # Combine all meshes
    combined = trimesh.util.concatenate([cube, cube2, sphere, sphere2, cylinder, torus])
    return combined, [cube, cube2, sphere, sphere2, cylinder, torus]


# Generate and show
mesh, items = create_primitive_meshes()

# Center on bottom-middle
bbox = mesh.bounds
center_xy = (bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2
mesh.apply_translation([-center_xy[0], -center_xy[1], -bbox[0][2]])

# Export to GLB or show
mesh.export("primitives.glb")
# mesh.show()  # Optional preview if pyglet is <2.0

# some boolean ops
# Boolean difference: cube - sphere
cutout = items[0].difference(items[2].apply_translation((-20, 0, 0)))

# Save result
cutout.export("cube_minus_half_sphere.glb")

# Move the cylinder to go through the cube along Z
items[4].apply_translation((0, 0, 0))  # Already centered at origin, passes through cube

# Attempt boolean subtraction (only works if backend is functional)
result = items[0].difference(items[4].apply_translation((-60, 0, 0)))
result.export("cube_with_hole.glb")

