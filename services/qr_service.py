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


def _get_font(size, bold=False):
    """Cross-platform font loader supporting Windows and Linux environments."""
    font_candidates = []
    if bold:
        font_candidates = [
            'arialbd.ttf', 'segoeuib.ttf', 'calibrib.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'DejaVuSans-Bold.ttf', 'DejaVuSans.ttf', 'arial.ttf'
        ]
    else:
        font_candidates = [
            'arial.ttf', 'segoeui.ttf', 'calibri.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            'DejaVuSans.ttf'
        ]

    windir = os.environ.get('WINDIR', 'C:\\Windows')
    for f in font_candidates:
        # Check Windows Fonts directory
        if not f.startswith('/'):
            win_p = os.path.join(windir, 'Fonts', f)
            if os.path.exists(win_p):
                try:
                    return ImageFont.truetype(win_p, size)
                except Exception:
                    pass
        # Check direct path or system font path
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def generate_qr_code(slug, employee_id=None, employee_name=None, designation=None, company_name=None, company_logo_path=None):
    """
    Generate standard PNG, SVG, and high-definition Branded JPEG/PNG Card for an employee profile.
    QR code encodes: {Config.BASE_URL}/q/{slug}
    """
    ensure_qr_directories()
    
    target_url = f"{Config.BASE_URL}/q/{slug}"
    
    png_filename = f"{slug}.png"
    svg_filename = f"{slug}.svg"
    branded_filename = f"{slug}_branded.png"
    card_jpg_filename = f"{slug}_card.jpg"
    
    png_full_path = Config.QR_PATH / png_filename
    svg_full_path = Config.QR_PATH / svg_filename
    branded_full_path = Config.QR_PATH / branded_filename
    card_jpg_full_path = Config.QR_PATH / card_jpg_filename
    
    # Relative paths stored in database
    png_rel_path = f"uploads/qr/{png_filename}"
    svg_rel_path = f"uploads/qr/{svg_filename}"
    branded_rel_path = f"uploads/qr/{branded_filename}"
    card_jpg_rel_path = f"uploads/qr/{card_jpg_filename}"

    # 1. Generate Standard PNG
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=14,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#0f172a", back_color="white").convert('RGB')
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

    # 3. Generate Branded High-Definition Photo Cards (JPEG & PNG)
    display_name = employee_name if employee_name else slug.capitalize()
    display_desig = designation if designation else "Digital Business Profile"
    display_company = company_name if company_name else "Nexalogic Techno"
    
    _create_branded_qr_image(
        qr_image=qr_img,
        output_png_path=branded_full_path,
        output_jpg_path=card_jpg_full_path,
        company_name=display_company,
        employee_name=display_name,
        designation=display_desig,
        slug=slug,
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
        'branded_png_path': branded_rel_path,
        'card_jpg_path': card_jpg_rel_path
    }


def _create_branded_qr_image(
    qr_image,
    output_png_path,
    output_jpg_path,
    company_name,
    employee_name,
    designation,
    slug="",
    company_logo_path=None
):
    """
    Renders an ultra-sharp, high-resolution 1080x1440 corporate digital badge/card.
    Contains full employee details: Name, Designation, Company, Verified Badge, and QR Code.
    Saves in both JPEG and PNG format.
    """
    card_width = 1080
    card_height = 1440
    
    # 1. Base executive dark background (#0b1120)
    card = Image.new('RGB', (card_width, card_height), (11, 17, 32))
    draw = ImageDraw.Draw(card)
    
    # Accent top border
    for i in range(14):
        draw.line([(0, i), (card_width, i)], fill=(79, 70, 229))

    # 2. Typography fonts
    font_badge = _get_font(22, bold=True)
    font_company = _get_font(34, bold=True)
    font_name = _get_font(52, bold=True)
    font_desig = _get_font(30, bold=False)
    font_cta = _get_font(26, bold=True)
    font_url = _get_font(24, bold=False)
    font_footer = _get_font(20, bold=False)

    # 3. Top Badges & Company Branding
    draw.text(
        (card_width // 2, 60),
        "OFFICIAL DIGITAL PROFILE • VERIFIED CARD",
        fill=(129, 140, 248),
        font=font_badge,
        anchor="mm"
    )
    
    # Clean uppercase company name
    clean_company = str(company_name or 'NEXALOGIC TECHNO').strip().upper()
    draw.text(
        (card_width // 2, 105),
        clean_company,
        fill=(226, 232, 240),
        font=font_company,
        anchor="mm"
    )
    
    # 4. White Container Card for QR Code
    box_w = 760
    box_h = 760
    box_x = (card_width - box_w) // 2
    box_y = 155
    
    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=36,
        fill=(255, 255, 255)
    )
    
    # Resize and place QR in center
    qr_display_size = 660
    resized_qr = qr_image.resize((qr_display_size, qr_display_size), Image.Resampling.LANCZOS)
    qr_x = box_x + (box_w - qr_display_size) // 2
    qr_y = box_y + (box_h - qr_display_size) // 2
    card.paste(resized_qr, (qr_x, qr_y))

    # Optional Logo overlay in center of QR
    if company_logo_path and os.path.exists(company_logo_path):
        try:
            logo = Image.open(company_logo_path).convert("RGBA")
            logo_size = 110
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            # White background behind logo
            logo_bg = Image.new('RGBA', (logo_size + 16, logo_size + 16), (255, 255, 255, 255))
            card.paste(logo_bg, (qr_x + (qr_display_size - logo_size - 16) // 2, qr_y + (qr_display_size - logo_size - 16) // 2))
            card.paste(logo, (qr_x + (qr_display_size - logo_size) // 2, qr_y + (qr_display_size - logo_size) // 2), mask=logo)
        except Exception:
            pass

    # 5. Employee Details Below QR
    name_y = box_y + box_h + 65
    draw.text((card_width // 2, name_y), str(employee_name or 'Team Member').strip(), fill=(255, 255, 255), font=font_name, anchor="mm")
    
    desig_y = name_y + 55
    draw.text((card_width // 2, desig_y), str(designation or 'Digital Profile').strip(), fill=(56, 189, 248), font=font_desig, anchor="mm")

    # 6. Action Button / Pill
    pill_w = 560
    pill_h = 64
    pill_x = (card_width - pill_w) // 2
    pill_y = desig_y + 50
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=32,
        fill=(79, 70, 229)
    )
    draw.text(
        (card_width // 2, pill_y + pill_h // 2),
        "SCAN TO CONNECT & LEAVE REVIEW",
        fill=(255, 255, 255),
        font=font_cta,
        anchor="mm"
    )

    # 7. URL Handle
    clean_domain = Config.BASE_URL.replace("https://", "").replace("http://", "").rstrip("/")
    profile_url_text = f"{clean_domain}/{slug}" if slug else clean_domain
    draw.text((card_width // 2, pill_y + pill_h + 40), profile_url_text, fill=(148, 163, 184), font=font_url, anchor="mm")

    # 8. Footer
    draw.text(
        (card_width // 2, card_height - 40),
        "Instant Contact • Direct WhatsApp • Verified GMB Reviews",
        fill=(100, 116, 139),
        font=font_footer,
        anchor="mm"
    )

    # 9. Save as both JPEG (high quality) and PNG
    try:
        card.save(str(output_jpg_path), format='JPEG', quality=95, optimize=True)
    except Exception:
        card.save(str(output_jpg_path), format='JPEG', quality=90)

    try:
        card.save(str(output_png_path), format='PNG', optimize=True)
    except Exception:
        card.save(str(output_png_path), format='PNG')
