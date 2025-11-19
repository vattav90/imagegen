from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont
import io
import math
import requests

app = Flask(__name__)

# --- Constants ---
MAX_POINTS = 14000
MAX_NIGHTS = 60

# --- ASSETS (Replace with your real URLs) ---
CARD_IMAGE_URL = "https://i.imgur.com/8Y9f14r.png" 
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"

def load_font(size):
    try:
        response = requests.get(FONT_URL, timeout=5)
        return ImageFont.truetype(io.BytesIO(response.content), size)
    except:
        return ImageFont.load_default()

def load_image_from_url(url):
    try:
        # Added timeout to prevent hanging
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()
        return Image.open(response.raw).convert("RGBA")
    except Exception as e:
        print(f"Failed to load image: {e}")
        return None

def draw_capped_arc(draw, cx, cy, radius, start_angle, end_angle, width, color):
    """Draws an arc with rounded caps."""
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(bbox, start=start_angle, end=end_angle, fill=color, width=width)
    
    cap_r = width / 2
    
    # Start Cap
    start_rad = math.radians(start_angle)
    sx = cx + radius * math.cos(start_rad)
    sy = cy + radius * math.sin(start_rad)
    draw.ellipse([sx - cap_r, sy - cap_r, sx + cap_r, sy + cap_r], fill=color)

    # End Cap
    end_rad = math.radians(end_angle)
    ex = cx + radius * math.cos(end_rad)
    ey = cy + radius * math.sin(end_rad)
    draw.ellipse([ex - cap_r, ey - cap_r, ex + cap_r, ey + cap_r], fill=color)

def generate_status_image(points, nights):
    # --- 1. SETUP (Transparent Canvas) ---
    TARGET_WIDTH, TARGET_HEIGHT = 600, 320
    SCALE_FACTOR = 8
    
    WIDTH = TARGET_WIDTH * SCALE_FACTOR
    HEIGHT = TARGET_HEIGHT * SCALE_FACTOR
    
    # Transparent Background
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # --- 2. Geometry & Colors ---
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT - (20 * SCALE_FACTOR) 
    
    RADIUS_OUTER = 250 * SCALE_FACTOR
    RADIUS_INNER = 190 * SCALE_FACTOR
    LINE_WIDTH = 24 * SCALE_FACTOR

    TEAL_BG = (230, 242, 245)
    INDIGO_BG = (227, 230, 238)
    TEAL_FG = (45, 228, 216)
    INDIGO_FG = (72, 94, 234)

    # --- 3. Draw Background Arches ---
    draw_capped_arc(draw, CENTER_X, CENTER_Y, RADIUS_OUTER, 180, 0, LINE_WIDTH, TEAL_BG)
    draw_capped_arc(draw, CENTER_X, CENTER_Y, RADIUS_INNER, 180, 0, LINE_WIDTH, INDIGO_BG)
    
    # --- 4. Draw Progress Arches ---
    points_progress = min(1.0, max(0.0, points / MAX_POINTS))
    nights_progress = min(1.0, max(0.0, nights / MAX_NIGHTS))
    
    points_end_angle = 180 + (180 * points_progress)
    nights_end_angle = 180 + (180 * nights_progress)
    
    if points_progress > 0:
        draw_capped_arc(draw, CENTER_X, CENTER_Y, RADIUS_OUTER, 180, points_end_angle, LINE_WIDTH, TEAL_FG)
    if nights_progress > 0:
        draw_capped_arc(draw, CENTER_X, CENTER_Y, RADIUS_INNER, 180, nights_end_angle, LINE_WIDTH, INDIGO_FG)

    # --- 5. Paste Card Image ---
    card_img = load_image_from_url(CARD_IMAGE_URL)
    card_target_width = 160 * SCALE_FACTOR
    
    # FIX: Initialize card_y with a default value so code doesn't crash if image fails
    # We assume a standard card ratio (approx 0.63 height/width) for the default
    default_card_height = int(card_target_width * 0.63)
    card_y = CENTER_Y - default_card_height - (10 * SCALE_FACTOR)

    if card_img:
        # Resize card to fit nicely inside the inner arc
        aspect_ratio = card_img.height / card_img.width
        card_target_height = int(card_target_width * aspect_ratio)
        
        card_img = card_img.resize((card_target_width, card_target_height), resample=Image.LANCZOS)
        
        # Calculate position to center it inside the arc
        card_x = CENTER_X - (card_target_width // 2)
        
        # UPDATE card_y with the REAL image height
        card_y = CENTER_Y - card_target_height - (10 * SCALE_FACTOR) 
        
        img.paste(card_img, (card_x, card_y), card_img)

    # --- 6. Draw Text "To achieve Platinum Status" ---
    font_size = 14 * SCALE_FACTOR
    font = load_font(font_size)
    
    text = "To achieve Platinum Status"
    
    # Get text size
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    # Position text above the card (using the safe card_y)
    text_x = CENTER_X - (text_width // 2)
    text_y = card_y - text_height - (20 * SCALE_FACTOR)
    
    # Draw Text (White)
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    # --- 7. Resize & Output ---
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), resample=Image.LANCZOS)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/generate-progress-image', methods=['GET'])
def serve_dynamic_image():
    try:
        p = int(request.args.get('points', 0))
        n = int(request.args.get('nights', 0))
    except:
        p, n = 0, 0
    return send_file(generate_status_image(p, n), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
