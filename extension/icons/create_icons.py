from PIL import Image, ImageDraw

def create_icon(size):
    # Create a new image with a white background
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a red circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='red')
    
    # Save the image
    image.save(f'icon{size}.png')

# Create icons of different sizes
for size in [16, 48, 128]:
    create_icon(size) 