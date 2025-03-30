from PIL import Image, ImageDraw
import numpy as np

def create_color_texture(filename, color, alpha=255, size=256):
    """Generate a solid color PNG texture."""
    img = Image.new("RGBA", (size, size), color + (alpha,))
    img.save(filename, format="PNG")



def create_hatch_texture(filename, pattern="diagonal", line_spacing=10, rotate_degrees=0):
    size = 256
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    if pattern == "diagonal":
        for i in range(-size, size * 2, line_spacing):
            draw.line([(i, 0), (i - size, size)], fill="black", width=2)

    elif pattern == "crosshatch":
        for i in range(0, size, line_spacing):
            draw.line([(i, 0), (i, size)], fill="black", width=2)
            draw.line([(0, i), (size, i)], fill="black", width=2)

    # Rotate if needed
    if rotate_degrees != 0:
        img = img.rotate(rotate_degrees, expand=True, fillcolor=(255, 255, 255, 0))
        # Crop back to center
        width, height = img.size
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))

    img.save(f"{filename}", format="PNG")

# Create variations
create_hatch_texture("hatch1.png", pattern="diagonal", line_spacing=8, rotate_degrees=0)
create_hatch_texture("hatch2.png", pattern="crosshatch", line_spacing=8, rotate_degrees=0)
create_hatch_texture("hatch3.png", pattern="diagonal", line_spacing=6, rotate_degrees=45)
create_hatch_texture("hatch4.png", pattern="crosshatch", line_spacing=6, rotate_degrees=30)

# Generate the textures
create_color_texture("yellow.png", (255, 255, 0))         # Bright yellow
create_color_texture("red.png", (192, 0, 0))             # Deep red (for metallic style)
create_color_texture("blue.png", (0, 128, 255), 128)  # Semi-transparent blue
