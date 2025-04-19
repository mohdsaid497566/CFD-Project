"""
Script to create placeholder images for the web UI
Uses PIL/Pillow to generate simple gradient images with text
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageColor

def create_gradient_image(filename, size, colors, text):
    """Create a gradient image with text"""
    # Create a new image with white background
    image = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(image)
    
    # Create gradient
    for y in range(size[1]):
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * y / size[1])
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * y / size[1])
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * y / size[1])
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    # Add text
    try:
        # Try to get a font
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        # If the specific font is not available, use default
        font = ImageFont.load_default()
    
    # Get text size
    text_width, text_height = draw.textsize(text, font=font)
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    # Draw text with black outline for better visibility
    draw.text((position[0]-1, position[1]), text, font=font, fill=(0, 0, 0))
    draw.text((position[0]+1, position[1]), text, font=font, fill=(0, 0, 0))
    draw.text((position[0], position[1]-1), text, font=font, fill=(0, 0, 0))
    draw.text((position[0], position[1]+1), text, font=font, fill=(0, 0, 0))
    draw.text(position, text, font=font, fill=(255, 255, 255))
    
    # Save the image
    image.save(filename)
    print(f"Created {filename}")

def main():
    # Ensure the images directory exists
    images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # Create model placeholder
    create_gradient_image(
        os.path.join(images_dir, 'model_placeholder.png'),
        (400, 300),
        [(0, 0, 150), (200, 200, 255)],
        "Model Preview"
    )
    
    # Create convergence placeholder
    create_gradient_image(
        os.path.join(images_dir, 'convergence_placeholder.png'),
        (400, 300),
        [(0, 100, 0), (200, 255, 100)],
        "Convergence Plot"
    )
    
    # Create result placeholder
    create_gradient_image(
        os.path.join(images_dir, 'result_placeholder.png'),
        (600, 400),
        [(150, 0, 0), (255, 200, 100)],
        "CFD Visualization"
    )
    
    # Create flow chart placeholder
    create_gradient_image(
        os.path.join(images_dir, 'flow_chart_placeholder.png'),
        (400, 300),
        [(100, 0, 100), (255, 200, 255)],
        "Flow Rate Chart"
    )
    
    print("All placeholder images created successfully!")

if __name__ == "__main__":
    main()
