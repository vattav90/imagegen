from flask import Flask, send_file, request
from PIL import Image, ImageDraw
import io
import math

app = Flask(__name__)

# --- Constants for Max Values ---
MAX_POINTS = 14000
MAX_NIGHTS = 60
# --------------------------------

def draw_progress_arch(draw, center_x, center_y, radius, progress_percent, line_width, color):
    """Draws a progress arc from 180 degrees down to 0 degrees based on percentage."""
    
    # Angles for the semi-circle
    FULL_ARCH_START = 180
    FULL_ARCH_END = 0
    total_degrees = FULL_ARCH_START - FULL_ARCH_END 
    
    # Calculate the angle where the progress stops
    progress_degrees = total_degrees * progress_percent
    current_end_angle = FULL_ARCH_START - progress_degrees
    
    # Bounding box for the arc
    bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
    
    # Draw the progress arc
    draw.arc(
        bbox, 
        start=current_end_angle, 
        end=FULL_ARCH_START,
        fill=color, 
        width=line_width
    )

def generate_status_image(points, nights):
    """
    Generates the progress bar image based on current points and nights.
    """
    WIDTH, HEIGHT = 400, 200
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Calculate Progress (clamped 0 to 1)
    points_progress = min(1.0, max(0.0, points / MAX_POINTS))
    nights_progress = min(1.0, max(0.0, nights / MAX_NIGHTS))

    # Parameters
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT 
    LINE_WIDTH = 15
    FULL_ARCH_START = 180 
    FULL_ARCH_END = 0
    
    # Colors
    TEAL_FG = (45, 228, 216)
    TEAL_BG = (230, 242, 245)
    INDIGO_FG = (72, 94, 234)
    INDIGO_BG = (227, 230, 238)
    
    RADIUS_OUTER = 170 
    RADIUS_INNER = 130 

    # 2. Draw Background Arches
    draw.arc([CENTER_X - RADIUS_OUTER, CENTER_Y - RADIUS_OUTER, CENTER_X + RADIUS_OUTER, CENTER_Y + RADIUS_OUTER],
             start=FULL_ARCH_END, end=FULL_ARCH_START, fill=TEAL_BG, width=LINE_WIDTH)
    draw.arc([CENTER_X - RADIUS_INNER, CENTER_Y - RADIUS_INNER, CENTER_X + RADIUS_INNER, CENTER_Y + RADIUS_INNER],
             start=FULL_ARCH_END, end=FULL_ARCH_START, fill=INDIGO_BG, width=LINE_WIDTH)
             
    # 3. Draw Progress Arches
    draw_progress_arch(draw, CENTER_X, CENTER_Y, RADIUS_OUTER, points_progress, LINE_WIDTH, TEAL_FG)
    draw_progress_arch(draw, CENTER_X, CENTER_Y, RADIUS_INNER, nights_progress, LINE_WIDTH, INDIGO_FG)

    # Return image as a byte stream
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


@app.route('/generate-progress-image', methods=['GET'])
def serve_dynamic_image():
    # Attempt to get 'points' and 'nights' from the query parameters
    try:
        current_points = int(request.args.get('points', 0))
        current_nights = int(request.args.get('nights', 0))
    except ValueError:
        # Handle case where inputs are not valid integers
        current_points = 0
        current_nights = 0
        
    image_stream = generate_status_image(current_points, current_nights)
    
    # Return the generated PNG file
    return send_file(image_stream, mimetype='image/png')


if __name__ == '__main__':
    # Use a secure, production-ready server (like Gunicorn/uWSGI) for actual deployment
    app.run(debug=True)
