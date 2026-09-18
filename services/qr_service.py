import os
import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from config import Config
from database.connection import query_db

def ensure_qr_directories():
    """Ensure the QR output directory exists."""
    Config.QR_PATH.mkdir(parents=True, exist_ok=True)


def generate_qr_code(slug, employee_id=None, employee_name=None, designation=None, company_name=None, company_logo_path=None):
    """
    Generate standard PNG, SVG, and Branded Card PNG for an employee profile.
    QR code encodes: {Config.BASE_URL}/q/{slug}
    """
    ensure_qr_directories()
    
    target_url = f"{Config.BASE_URL}/q/{slug}"
    
    png_filename = f"{slug}.png"
    svg_filename = f"{slug}.svg"
    branded_filename = f"{slug}_branded.png"
    
    png_full_path = Config.QR_PATH / png_filename
    svg_full_path = Config.QR_PATH / svg_filename
    branded_full_path = Config.QR_PATH / branded_filename
    
    # Relative paths stored in database
    png_rel_path = f"uploads/qr/{png_filename}"
    svg_rel_path = f"uploads/qr/{svg_filename}"
    branded_rel_path = f"uploads/qr/{branded_filename}"

    # 1. Generate Standard PNG
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#1e1b4b", back_color="white").convert('RGB')
    qr_img.save(str(png_full_path), format='PNG')

    # 2. Generate SVG
    svg_factory = qrcode.image.svg.SvgPathImage
    svg_qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
        image_factory=svg_factory
    )
    svg_qr.add_data(target_url)
    svg_qr.make(fit=True)
    svg_img = svg_qr.make_image()
    with open(str(svg_full_path), 'wb') as f:
        svg_img.save(f)

    # 3. Generate Branded Card PNG
    display_name = employee_name if employee_name else slug.capitalize()
    display_desig = designation if designation else "Digital Profile"
    display_company = company_name if company_name else "Apex Innovations"
    
    _create_branded_qr_image(
        qr_image=qr_img,
        output_path=branded_full_path,
        company_name=display_company,
        employee_name=display_name,
        designation=display_desig,
        company_logo_path=company_logo_path
    )

    # 4. Upsert in database if employee_id is provided
    if employee_id:
        existing = query_db(
            "SELECT id FROM qr_codes WHERE employee_id = %s",
            (employee_id,),
            one=True
        )
        if existing:
            query_db(
                """
                UPDATE qr_codes 
                SET qr_url = %s, png_path = %s, svg_path = %s, branded_png_path = %s, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = %s
                """,
                (target_url, png_rel_path, svg_rel_path, branded_rel_path, employee_id),
                commit=True
            )
        else:
            query_db(
                """
                INSERT INTO qr_codes (employee_id, qr_url, png_path, svg_path, branded_png_path)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (employee_id, target_url, png_rel_path, svg_rel_path, branded_rel_path),
                commit=True
            )

    return {
        'qr_url': target_url,
        'png_path': png_rel_path,
        'svg_path': svg_rel_path,
        'branded_png_path': branded_rel_path
    }


def _create_branded_qr_image(qr_image, output_path, company_name, employee_name, designation, company_logo_path=None):
    """
    Renders a high-res, beautifully branded corporate card for print or digital sharing.
    """
    card_width = 800
    card_height = 1100
    
    # Create canvas with rich gradient-styled background
    card = Image.new('RGBA', (card_width, card_height), (15, 23, 42, 255)) # Slate 900
    draw = ImageDraw.Draw(card)
    
    # Header bar accent
    draw.rectangle([(0, 0), (card_width, 14)], fill=(79, 70, 229, 255)) # Indigo 600
    
    # Try to load default fonts or fall back to default
    try:
        font_company = ImageFont.truetype("arial.ttf", 32)
        font_title = ImageFont.truetype("arialbd.ttf", 40)
        font_subtitle = ImageFont.truetype("arial.ttf", 26)
        font_cta = ImageFont.truetype("arialbd.ttf", 28)
        font_footer = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_company = ImageFont.load_default()
        font_title = font_company
        font_subtitle = font_company
        font_cta = font_company
        font_footer = font_company

    # 1. Company Name Header
    draw.text((card_width // 2, 70), company_name.upper(), fill=(148, 163, 184), font=font_company, anchor="mm")
    
    # 2. White Container Card for QR Code
    box_margin = 80
    box_top = 130
    box_width = card_width - (2 * box_margin) # 640
    box_height = 640
    box_bottom = box_top + box_height
    
    draw.rounded_rectangle(
        [(box_margin, box_top), (box_margin + box_width, box_bottom)],
        radius=28,
        fill=(255, 255, 255, 255)
    )
    
    # Resize QR to fit nicely in white container
    qr_size = 500
    resized_qr = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    qr_x = box_margin + (box_width - qr_size) // 2
    qr_y = box_top + (box_height - qr_size) // 2
    card.paste(resized_qr, (qr_x, qr_y))

    # Optional Logo overlay in center of QR
    if company_logo_path and os.path.exists(company_logo_path):
        try:
            logo = Image.open(company_logo_path).convert("RGBA")
            logo_size = 90
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            # White background behind logo
            logo_bg = Image.new('RGBA', (logo_size + 12, logo_size + 12), (255, 255, 255, 255))
            card.paste(logo_bg, (qr_x + (qr_size - logo_size - 12) // 2, qr_y + (qr_size - logo_size - 12) // 2))
            card.paste(logo, (qr_x + (qr_size - logo_size) // 2, qr_y + (qr_size - logo_size) // 2), mask=logo)
        except Exception:
            pass

    # 3. Employee Name & Designation
    name_y = box_bottom + 65
    draw.text((card_width // 2, name_y), employee_name, fill=(248, 250, 252), font=font_title, anchor="mm")
    
    desig_y = name_y + 45
    draw.text((card_width // 2, desig_y), designation, fill=(148, 163, 184), font=font_subtitle, anchor="mm")

    # 4. CTA Badge
    cta_y = desig_y + 70
    cta_text = "SCAN TO CONNECT & REVIEW"
    
    # Pill background for CTA
    cta_w = 460
    cta_h = 56
    cta_left = (card_width - cta_w) // 2
    draw.rounded_rectangle(
        [(cta_left, cta_y - cta_h // 2), (cta_left + cta_w, cta_y + cta_h // 2)],
        radius=28,
        fill=(79, 70, 229, 255)
    )
    draw.text((card_width // 2, cta_y), cta_text, fill=(255, 255, 255), font=font_cta, anchor="mm")

    # 5. Footer branding
    draw.text((card_width // 2, card_height - 40), "Official Digital Card • Verified Profile", fill=(100, 116, 139), font=font_footer, anchor="mm")

    # Convert to RGB and save
    final_card = card.convert('RGB')
    final_card.save(str(output_path), format='PNG', quality=95)
