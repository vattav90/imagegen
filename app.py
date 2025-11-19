from flask import Flask, send_file, request
from PIL import Image, ImageDraw
import io

app = Flask(__name__)

# --- Constants ---
MAX_POINTS = 14000
MAX_NIGHTS = 60

def generate_status_image(points, nights):
    # --- 1. SUPERSAMPLING SETUP ---
    # We draw everything 4x larger to make it smooth, then resize down.
    TARGET_WIDTH, TARGET_HEIGHT = 400, 220
    SCALE_FACTOR = 4
    
    WIDTH = TARGET_WIDTH * SCALE_FACTOR
    HEIGHT = TARGET_HEIGHT * SCALE_FACTOR
    
    # Background color to match the email template (Beige)
    BG_COLOR = (226, 192, 156, 255) 
    
    img = Image.new('RGBA', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # --- 2. Calculate Progress ---
    points_progress = min(1.0, max(0.0, points / MAX_POINTS))
    nights_progress = min(1.0, max(0.0, nights / MAX_NIGHTS))

    # --- 3. Scaled Geometry Parameters ---
    # Everything must be multiplied by SCALE_FACTOR
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT - (20 * SCALE_FACTOR)
    
    RADIUS_OUTER = 160 * SCALE_FACTOR
    RADIUS_INNER = 120 * SCALE_FACTOR
    LINE_WIDTH = 18 * SCALE_FACTOR

    # Colors
    TEAL_BG = (230, 242, 245)
    INDIGO_BG = (227, 230, 238)
    TEAL_FG = (45, 228, 216)
    INDIGO_FG = (72, 94, 234)

    # --- 4. Draw Arches (180 to 0 degrees) ---
    
    # Backgrounds
    draw.arc(
        [CENTER_X - RADIUS_OUTER, CENTER_Y - RADIUS_OUTER, CENTER_X + RADIUS_OUTER, CENTER_Y + RADIUS_OUTER],
        start=180, end=0, fill=TEAL_BG, width=LINE_WIDTH
    )
    draw.arc(
        [CENTER_X - RADIUS_INNER, CENTER_Y - RADIUS_INNER, CENTER_X + RADIUS_INNER, CENTER_Y + RADIUS_INNER],
        start=180, end=0, fill=INDIGO_BG, width=LINE_WIDTH
    )
             
    # Dynamic Progress
    points_end_angle = 180 + (180 * points_progress)
    nights_end_angle = 180 + (180 * nights_progress)
    
    if points_progress > 0:
        draw.arc(
            [CENTER_X - RADIUS_OUTER, CENTER_Y - RADIUS_OUTER, CENTER_X + RADIUS_OUTER, CENTER_Y + RADIUS_OUTER],
            start=180, end=points_end_angle, fill=TEAL_FG, width=LINE_WIDTH
        )
    
    if nights_progress > 0:
        draw.arc(
            [CENTER_X - RADIUS_INNER, CENTER_Y - RADIUS_INNER, CENTER_X + RADIUS_INNER, CENTER_Y + RADIUS_INNER],
            start=180, end=nights_end_angle, fill=INDIGO_FG, width=LINE_WIDTH
        )

    # --- 5. RESIZE AND RETURN ---
    # High-quality resize to smooth the edges (Anti-aliasing)
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), resample=Image.LANCZOS)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

@app.route('/generate-progress-image', methods=['GET'])
def serve_dynamic_image():
    try:
        current_points = int(request.args.get('points', 0))
        current_nights = int(request.args.get('nights', 0))
    except ValueError:
        current_points = 0
        current_nights = 0
        
    image_stream = generate_status_image(current_points, current_nights)
    return send_file(image_stream, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
