import trimesh

# use with manifold3d: pip install manifold3d =>  default engine

# Create base cube
cube = trimesh.creation.box(extents=(20, 20, 20))

# Create sphere and position it halfway into cube
sphere = trimesh.creation.icosphere(radius=10, subdivisions=3)
sphere.apply_translation((10, 0, 0))  # Half inside the cube (X=10 is edge of cube)

# Boolean difference: cube - sphere
cutout = cube.difference(sphere)
#cutout = sphere.difference(cube)

# Save or view result
cutout.export("cube_minus_half_sphere.glb")

# Create a cube
cube = trimesh.creation.box(extents=(20, 20, 20))

# Create a cylinder to represent the hole
cylinder = trimesh.creation.cylinder(radius=5, height=25, sections=64)
cylinder.apply_translation((0, 0, 0))  # Centered

# Move the cylinder to go through the cube along Z
cylinder.apply_translation((0, 0, 0))  # Already centered at origin, passes through cube

# Attempt boolean subtraction (only works if backend is functional)
result = cube.difference(cylinder)
result.export("cube_with_hole.glb")

