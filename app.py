from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

# --- Constants ---
MAX_POINTS = 14000
MAX_NIGHTS = 60

def generate_status_image(points, nights):
    """
    Generates the progress bar image based on current points and nights.
    """
    WIDTH, HEIGHT = 400, 220  # Slightly taller to accommodate stroke width
    
    # 1. Setup Image with Beige Background (Matches your design)
    # Use 'RGBA' and color (226, 192, 156) for the beige look, or 'white'
    img = Image.new('RGBA', (WIDTH, HEIGHT), (226, 192, 156, 255)) 
    draw = ImageDraw.Draw(img)
    
    # 2. Calculate Progress (clamped 0 to 1)
    points_progress = min(1.0, max(0.0, points / MAX_POINTS))
    nights_progress = min(1.0, max(0.0, nights / MAX_NIGHTS))

    # 3. Geometry Parameters
    # Center at the bottom middle
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT - 20 
    
    # Radii
    RADIUS_OUTER = 160 
    RADIUS_INNER = 120 
    LINE_WIDTH = 18

    # 4. Draw Background Arches (Top Semicircle: 180 to 0)
    # Pillow angles: 180=Left, 270=Top, 0=Right (Clockwise)
    
    TEAL_BG = (230, 242, 245)
    INDIGO_BG = (227, 230, 238)
    
    # Draw Outer Background (Teal) - Start 180, End 0
    draw.arc(
        [CENTER_X - RADIUS_OUTER, CENTER_Y - RADIUS_OUTER, CENTER_X + RADIUS_OUTER, CENTER_Y + RADIUS_OUTER],
        start=180, end=0, fill=TEAL_BG, width=LINE_WIDTH
    )

    # Draw Inner Background (Indigo) - Start 180, End 0
    draw.arc(
        [CENTER_X - RADIUS_INNER, CENTER_Y - RADIUS_INNER, CENTER_X + RADIUS_INNER, CENTER_Y + RADIUS_INNER],
        start=180, end=0, fill=INDIGO_BG, width=LINE_WIDTH
    )
             
    # 5. Draw Progress Arches (Dynamic)
    # We draw from 180 (Left) upwards to the right
    
    TEAL_FG = (45, 228, 216)
    INDIGO_FG = (72, 94, 234)
    
    # Calculate end angles based on progress
    # 180 is start. Full sweep is 180 degrees.
    points_end_angle = 180 + (180 * points_progress)
    nights_end_angle = 180 + (180 * nights_progress)
    
    # Draw Outer Progress
    if points_progress > 0:
        draw.arc(
            [CENTER_X - RADIUS_OUTER, CENTER_Y - RADIUS_OUTER, CENTER_X + RADIUS_OUTER, CENTER_Y + RADIUS_OUTER],
            start=180, end=points_end_angle, fill=TEAL_FG, width=LINE_WIDTH
        )
    
    # Draw Inner Progress
    if nights_progress > 0:
        draw.arc(
            [CENTER_X - RADIUS_INNER, CENTER_Y - RADIUS_INNER, CENTER_X + RADIUS_INNER, CENTER_Y + RADIUS_INNER],
            start=180, end=nights_end_angle, fill=INDIGO_FG, width=LINE_WIDTH
        )

    # Return image
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


@app.route('/generate-progress-image', methods=['GET'])
def serve_dynamic_image():
    try:
        # Get params, default to 0 if missing
        current_points = int(request.args.get('points', 0))
        current_nights = int(request.args.get('nights', 0))
    except ValueError:
        current_points = 0
        current_nights = 0
        
    image_stream = generate_status_image(current_points, current_nights)
    return send_file(image_stream, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)
