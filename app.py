from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import math
import os

app = Flask(__name__)

# --- Constants ---
# Note: In a full production app, these MAX values usually change based on the tier.
# For now, we keep them fixed or you can make them dynamic inputs as well.
MAX_POINTS = 14000
MAX_NIGHTS = 60

# --- FONT FILENAME ---
FONT_FILENAME = "font.ttf" 

def load_local_font(filename, size):
    """Loads a font from the local file system."""
    try:
        if not os.path.exists(filename):
            return ImageFont.load_default()
        return ImageFont.truetype(filename, size)
    except Exception as e:
        print(f"Error loading font {filename}: {e}")
        return ImageFont.load_default()

def load_local_image(filename, target_size=None, quality=Image.LANCZOS):
    """Loads an image from the local file system."""
    try:
        if not os.path.exists(filename):
            # print(f"Debug: {filename} not found.") # Uncomment for debugging
            return None
        img = Image.open(filename).convert("RGBA")
        if target_size:
            img = img.resize(target_size, resample=quality)
        return img
    except Exception as e:
        print(f"Error loading local image {filename}: {e}")
        return None

def draw_capped_arc(draw, cx, cy, radius, start_angle, end_angle, width, color):
    """Draws an arc with rounded caps."""
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(bbox, start=start_angle, end=end_angle, fill=color, width=width)
    
    center_radius = radius - (width / 2)
    cap_r = width / 2
    
    # Draw Start Cap
    start_rad = math.radians(start_angle)
    sx = cx + center_radius * math.cos(start_rad)
    sy = cy + center_radius * math.sin(start_rad)
    draw.ellipse([sx - cap_r, sy - cap_r, sx + cap_r, sy + cap_r], fill=color)

    # Draw End Cap
    end_rad = math.radians(end_angle)
    ex = cx + center_radius * math.cos(end_rad)
    ey = cy + center_radius * math.sin(end_rad)
    draw.ellipse([ex - cap_r, ey - cap_r, ex + cap_r, ey + cap_r], fill=color)

def get_tier_assets(tier):
    """
    Returns (next_tier_name, card_filename) based on the CURRENT tier.
    Mapping based on user request:
    Classic -> Silver Card
    Silver -> Gold Card
    Gold -> Platinum Card
    Platinum -> Diamond Card
    """
    t = tier.lower().strip()
    
    # Default fallback
    next_tier = "Diamond"
    card_file = "card_diamond.png"
    
    if t == "classic":
        next_tier = "Silver"
        card_file = "card_silver.png" # Corresponds to silver.svg
    elif t == "silver":
        next_tier = "Gold"
        card_file = "card_gold.png"   # Corresponds to gold.svg
    elif t == "gold":
        next_tier = "Platinum"
        card_file = "card_platinum.png" # Corresponds to platinum.svg
    elif t == "platinum":
        next_tier = "Diamond"
        card_file = "card_diamond.png"  # Corresponds to diamond.svg
        
    return next_tier, card_file

def generate_status_image(tier, reward_points, discount_val, status_points, nights):
    # --- 1. SETUP CANVAS ---
    TARGET_WIDTH = 600
    SCALE_FACTOR = 8 
    
    bg_filename = "bg3.png"
    target_height = 400 
    
    if os.path.exists(bg_filename):
        try:
            with Image.open(bg_filename) as temp_bg:
                aspect_ratio = temp_bg.height / temp_bg.width
                target_height = int(TARGET_WIDTH * aspect_ratio)
        except Exception as e:
            target_height = 400

    TARGET_HEIGHT = target_height
    WIDTH = TARGET_WIDTH * SCALE_FACTOR
    HEIGHT = TARGET_HEIGHT * SCALE_FACTOR
    
    bg_img = load_local_image("bg3.png", (WIDTH, HEIGHT))
    if not bg_img:
        bg_img = Image.new('RGBA', (WIDTH, HEIGHT), (226, 192, 156, 255))

    # --- 1.5 APPLY TIER MASKING ---
    # Mask colors based on current tier
    tier_colors = {
        "classic": "#050033",
        "silver": "#76777A",
        "gold": "#AF913A",
        "platinum": "#394049",
        "diamond": "#BABABA"
    }
    
    t_key = tier.lower().strip()
    hex_color = tier_colors.get(t_key, "#AF913A") # Default to Gold color if unknown
    
    # Convert hex to RGB
    rgb_color = ImageColor.getrgb(hex_color)
    
    # Create a solid color layer with 40% opacity (255 * 0.40 ≈ 102)
    mask_alpha = 102
    mask_color = rgb_color + (mask_alpha,)
    
    mask_layer = Image.new('RGBA', bg_img.size, mask_color)
    
    # Composite the mask over the background
    # This tints the background with the tier color
    bg_img = Image.alpha_composite(bg_img, mask_layer)
        
    img = bg_img.copy()
    draw = ImageDraw.Draw(img)
    
    # --- 2. FONT LOADING & HELPERS ---
    def draw_bold_text(xy, text, font, fill="white", strength=1.0, letter_spacing=0):
        stroke_w = int(strength * SCALE_FACTOR)
        x, y = xy
        
        if letter_spacing == 0:
            draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=fill)
        else:
            for char in text:
                draw.text((x, y), char, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=fill)
                try:
                    char_width = font.getlength(char)
                except AttributeError:
                    bbox = draw.textbbox((0,0), char, font=font)
                    char_width = bbox[2] - bbox[0]
                x += char_width + letter_spacing

    def get_spaced_text_size(text, font, letter_spacing=0):
        bbox = draw.textbbox((0, 0), text, font=font)
        base_height = bbox[3] - bbox[1]
        if letter_spacing == 0:
            return bbox[2] - bbox[0], base_height
        total_width = 0
        for i, char in enumerate(text):
            try:
                w = font.getlength(char)
            except AttributeError:
                b = draw.textbbox((0,0), char, font=font)
                w = b[2] - b[0]
            total_width += w
        if len(text) > 1:
            total_width += (len(text) - 1) * letter_spacing
        return total_width, base_height

    font_gold = load_local_font(FONT_FILENAME, 36 * SCALE_FACTOR)
    font_points = load_local_font(FONT_FILENAME, 28 * SCALE_FACTOR)
    font_discount = load_local_font(FONT_FILENAME, 10 * SCALE_FACTOR)
    font_achieve = load_local_font(FONT_FILENAME, 10 * SCALE_FACTOR)
    font_status_data = load_local_font(FONT_FILENAME, 20 * SCALE_FACTOR)
    font_status_label = load_local_font(FONT_FILENAME, 10 * SCALE_FACTOR)

    # --- 3. DRAW TOP TEXT ---
    current_y = 30 * SCALE_FACTOR  

    # A. TIER Text (Dynamic based on 'tier' variable)
    tier_text = tier.upper()
    tier_spacing = 3 * SCALE_FACTOR 
    
    gold_w, gold_h = get_spaced_text_size(tier_text, font_gold, tier_spacing)
    draw_bold_text(((WIDTH - gold_w) // 2, current_y), tier_text, font=font_gold, letter_spacing=tier_spacing)
    
    current_y += 1.5*gold_h + (10 * SCALE_FACTOR) 

    # B. Reward Points (Dynamic 'reward_points' variable)
    # Assuming reward_points input is a clean number/string. Formatting commas if it's an int.
    try:
        rp_formatted = f"{int(reward_points):,}"
    except:
        rp_formatted = str(reward_points)
        
    points_text = f"{rp_formatted} Reward Points"
    points_spacing = 1.5 * SCALE_FACTOR 
    points_w, points_h = get_spaced_text_size(points_text, font_points, 0)
    draw_bold_text(((WIDTH - points_w) // 2, current_y), points_text, font=font_points, letter_spacing=points_spacing)
    
    current_y += points_h + (10 * SCALE_FACTOR) 

    # C. Discount (Dynamic 'discount_val' variable)
    discount_text = f"or £{discount_val} discount on your next stay"
    discount_w, discount_h = get_spaced_text_size(discount_text, font_discount, 0)
    draw_bold_text(((WIDTH - discount_w) // 2, current_y), discount_text, font=font_discount, strength=0.5)
    
    current_y += 7*discount_h + (25 * SCALE_FACTOR) 

    # --- 4. ARC LAYOUT ---
    RADIUS_OUTER = 200 * SCALE_FACTOR 
    RADIUS_INNER = 155 * SCALE_FACTOR 
    LINE_WIDTH = 24 * SCALE_FACTOR

    ARC_CENTER_X = WIDTH // 2
    ARC_CENTER_Y = current_y + RADIUS_OUTER 
    
    # --- 5. DRAW ARCS (Using 'status_points' and 'nights') ---
    TEAL_BG = (230, 242, 245)
    INDIGO_BG = (227, 230, 238)
    TEAL_FG = (45, 228, 216)
    INDIGO_FG = (72, 94, 234)

    draw_capped_arc(draw, ARC_CENTER_X, ARC_CENTER_Y, RADIUS_OUTER, 180, 0, LINE_WIDTH, TEAL_BG)
    draw_capped_arc(draw, ARC_CENTER_X, ARC_CENTER_Y, RADIUS_INNER, 180, 0, LINE_WIDTH, INDIGO_BG)
    
    # Calculate progress
    try:
        sp_int = int(status_points)
        n_int = int(nights)
    except:
        sp_int = 0
        n_int = 0

    points_progress = min(1.0, max(0.0, sp_int / MAX_POINTS))
    nights_progress = min(1.0, max(0.0, n_int / MAX_NIGHTS))
    
    points_end_angle = 180 + (180 * points_progress)
    nights_end_angle = 180 + (180 * nights_progress)
    
    if points_progress > 0:
        draw_capped_arc(draw, ARC_CENTER_X, ARC_CENTER_Y, RADIUS_OUTER, 180, points_end_angle, LINE_WIDTH, TEAL_FG)
    if nights_progress > 0:
        draw_capped_arc(draw, ARC_CENTER_X, ARC_CENTER_Y, RADIUS_INNER, 180, nights_end_angle, LINE_WIDTH, INDIGO_FG)

    # --- 6. DRAW ICONS ---
    icon_size = 24 * SCALE_FACTOR 
    padded_icon_size = icon_size + (8 * SCALE_FACTOR) 
    border_width = 2 * SCALE_FACTOR 
    GOLDEN_COLOR = (255, 215, 0, 255) 

    def paste_icon(icon_name, angle, radius, color_layer):
        base_icon = load_local_image(icon_name, (icon_size, icon_size))
        if base_icon:
            composite_icon = Image.new('RGBA', (padded_icon_size, padded_icon_size), (0, 0, 0, 0))
            draw_composite = ImageDraw.Draw(composite_icon)

            circle_bbox = [0, 0, padded_icon_size, padded_icon_size]
            draw_composite.ellipse(circle_bbox, fill=(255, 255, 255, 255)) 
            draw_composite.ellipse(circle_bbox, outline=GOLDEN_COLOR, width=border_width)

            icon_offset_x = (padded_icon_size - icon_size) // 2
            icon_offset_y = (padded_icon_size - icon_size) // 2
            composite_icon.paste(base_icon, (icon_offset_x, icon_offset_y), base_icon)

            center_r = radius - (LINE_WIDTH / 2)
            rad = math.radians(angle)
            ex = ARC_CENTER_X + center_r * math.cos(rad)
            ey = ARC_CENTER_Y + center_r * math.sin(rad)
            
            dest_x = int(ex - padded_icon_size / 2)
            dest_y = int(ey - padded_icon_size / 2)
            
            img.paste(composite_icon, (dest_x, dest_y), composite_icon)

    paste_icon("iconA.png", points_end_angle, RADIUS_OUTER, TEAL_FG)
    paste_icon("iconC.png", nights_end_angle, RADIUS_INNER, INDIGO_FG)

    # --- 7. INTERNAL CONTENT (Dynamic Text + Dynamic Card) ---
    
    # Determine assets based on Tier
    next_tier_name, card_filename = get_tier_assets(tier)

    achieve_text = f"To achieve {next_tier_name} Status"
    achieve_w, achieve_h = get_spaced_text_size(achieve_text, font_achieve, 0)
    
    achieve_y = ARC_CENTER_Y - (RADIUS_INNER * 0.60) 
    
    draw_bold_text(((WIDTH - achieve_w) // 2, achieve_y), achieve_text, font=font_achieve, strength=0.5)

    # Dynamic Card Image
    # Note: Looks for card_silver.png, card_gold.png etc based on inputs
    card_img = load_local_image(card_filename)
    
    # Fallback to "card.png" if specific tier card not found
    if not card_img and card_filename != "card.png":
        card_img = load_local_image("card.png")

    card_bottom_y = 0
    
    if card_img:
        card_target_width = 110 * SCALE_FACTOR 
        aspect = card_img.height / card_img.width
        card_target_height = int(card_target_width * aspect)
        card_img = card_img.resize((card_target_width, card_target_height), resample=Image.LANCZOS)
        
        card_x = (WIDTH - card_target_width) // 2
        card_y = achieve_y + achieve_h + (15 * SCALE_FACTOR)
        
        img.paste(card_img, (card_x, int(card_y)), card_img)
        card_bottom_y = card_y + card_target_height
    else:
        # Fallback spacing if no card loads
        card_bottom_y = achieve_y + achieve_h + (100 * SCALE_FACTOR)

    # --- 8. BOTTOM STATS ---
    
    start_stats_y = card_bottom_y + (20 * SCALE_FACTOR)
    
    row_icon_size = 20 * SCALE_FACTOR
    icon_gap = 8 * SCALE_FACTOR
    text_gap = 8 * SCALE_FACTOR
    
    def create_white_bg_icon(filename, size):
        base = load_local_image(filename, (size, size))
        if not base: return None
        padding = 8 * SCALE_FACTOR
        bg_size = size + padding
        container = Image.new('RGBA', (bg_size, bg_size), (0,0,0,0))
        draw_bg = ImageDraw.Draw(container)
        draw_bg.ellipse([0,0,bg_size, bg_size], fill="white")
        offset = padding // 2
        container.paste(base, (offset, offset), base)
        return container

    icon_p_small = create_white_bg_icon("iconA.png", row_icon_size)
    icon_n_small = create_white_bg_icon("iconC.png", row_icon_size)

    def draw_stats_row(y_pos, data_text, label_text, icon_img):
        w_d, h_d = get_spaced_text_size(data_text, font_status_data, 0)
        w_l, h_l = get_spaced_text_size(label_text, font_status_label, 0)
        
        img_w = icon_img.width if icon_img else 0
        img_h = icon_img.height if icon_img else 0
        
        total_width = w_d + w_l + text_gap
        if icon_img:
            total_width += img_w + icon_gap
            
        current_x = (WIDTH - total_width) // 2

        try:
            ascent_d, _ = font_status_data.getmetrics()
            ascent_l, _ = font_status_label.getmetrics()
            baseline_offset = ascent_d - ascent_l
        except AttributeError:
            baseline_offset = h_d - h_l 

        if icon_img:
            icon_y = y_pos + (h_d // 2) - (img_h // 3)
            img.paste(icon_img, (int(current_x), int(icon_y)), icon_img)
            current_x += img_w + icon_gap
            
        draw_bold_text((current_x, y_pos), data_text, font=font_status_data, letter_spacing=points_spacing)
        current_x += w_d + text_gap
        draw_bold_text((current_x, y_pos + baseline_offset), label_text, font=font_status_label, strength=0.5)
        
        return h_d

    # Draw Points Row (Using 'status_points')
    try:
        p_data = f"{int(status_points):,}"
    except:
        p_data = str(status_points)

    p_label = f"/ {MAX_POINTS:,} Status points"
    row_h = draw_stats_row(1.05*start_stats_y, p_data, p_label, icon_p_small)
    
    # Draw Nights Row (Using 'nights')
    n_y = start_stats_y + 2.8*row_h + (10 * SCALE_FACTOR)
    n_data = f"{nights}"
    n_label = f"/ {MAX_NIGHTS} nights"
    draw_stats_row(n_y, n_data, n_label, icon_n_small)

    # --- 9. OUTPUT ---
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), resample=Image.LANCZOS)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/generate-progress-image', methods=['GET'])
def serve_dynamic_image():
    try:
        # Retrieve new parameters
        tier = request.args.get('tier', 'Gold') # Default to Gold
        reward_points = request.args.get('reward_points', '0')
        discount = request.args.get('discount', '0')
        status_points = request.args.get('status_points', '0')
        nights = request.args.get('nights', '0')
    except Exception as e:
        print(f"Error parsing args: {e}")
        tier, reward_points, discount, status_points, nights = 'Gold', 0, 0, 0, 0
        
    return send_file(
        generate_status_image(tier, reward_points, discount, status_points, nights), 
        mimetype='image/png'
    )

if __name__ == '__main__':
    app.run(debug=True)
