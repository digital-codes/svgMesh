import trimesh
import numpy as np

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

    """Create a non-uniformly scaled sphere (ellipsoid)."""
    sphere2_scale_factors=(1.0, 1.5, 0.75)
    sphere2.apply_scale(sphere2_scale_factors)
    # Combine all meshes
    combined = trimesh.util.concatenate([cube, cube2, sphere, sphere2, cylinder, torus])
    return combined

# Generate and show
mesh = create_primitive_meshes()

# Center on bottom-middle
bbox = mesh.bounds
center_xy = (bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2
mesh.apply_translation([-center_xy[0], -center_xy[1], -bbox[0][2]])

# Export to GLB or show
mesh.export("primitives.glb")
# mesh.show()  # Optional preview if pyglet is <2.0
