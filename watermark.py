from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

# =========================
# PENGATURAN WATERMARK
# =========================
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
FOLDER_INPUT = BASE_DIR / "foto_input"
FOLDER_OUTPUT = BASE_DIR / "foto_hasil"
FILE_LOGO = BASE_DIR / "logo.png"

TEKS_WATERMARK = "HUMASSMKN1STABAT"
OPACITY = 51                  # 20% dari 255
LOGO_WIDTH_RATIO = 0.08       # logo lebih kecil: 8% lebar foto
TEXT_SIZE = 10                # ukuran cadangan jika logo tidak tersedia
TEXT_TO_LOGO_HEIGHT_RATIO = 0.90  # teks sedikit lebih kecil daripada tinggi logo
GAP_RATIO = 0.008             # jarak vertikal logo ke tulisan
SHADOW = False
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_font(size: int):
    """Gunakan Anton jika file font tersedia; selain itu coba font umum."""
    candidates = [
        BASE_DIR / "Anton-Regular.ttf",
        Path("Anton-Regular.ttf"),
        Path("C:/Windows/Fonts/Anton-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("DejaVuSans-Bold.ttf"),
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    print("[PERINGATAN] Font Anton tidak ditemukan. Menggunakan font bawaan.")
    return ImageFont.load_default()


def load_logo(path: Path):
    """Muat logo dengan transparansi jika file logo tersedia."""
    if not path.is_file():
        print(f"[PERINGATAN] Logo tidak ditemukan: {path}. Watermark teks saja digunakan.")
        return None

    try:
        logo = Image.open(path).convert("RGBA")
        bbox = logo.getchannel("A").getbbox()
        if bbox:
            logo = logo.crop(bbox)
        return logo
    except Exception as exc:
        print(f"[PERINGATAN] Logo gagal dibaca ({exc}). Watermark teks saja digunakan.")
        return None


def add_watermark(image_path: Path, output_path: Path, logo_original):
    """Tambahkan logo di atas teks, sebagai satu kelompok di tengah bawah foto."""
    with Image.open(image_path) as source:
        photo = ImageOps.exif_transpose(source).convert("RGBA")

    width, height = photo.size
    short_side = min(width, height)

    logo = None
    logo_w = logo_h = 0
    if logo_original is not None:
        target_logo_w = max(1, int(width * LOGO_WIDTH_RATIO))
        scale = target_logo_w / logo_original.width
        target_logo_h = max(1, int(logo_original.height * scale))

        # Batasi tinggi logo agar tidak terlalu besar pada foto portrait.
        max_logo_h = max(1, int(height * 0.15))
        if target_logo_h > max_logo_h:
            scale = max_logo_h / logo_original.height
            target_logo_w = max(1, int(logo_original.width * scale))
            target_logo_h = max_logo_h

        logo = logo_original.resize(
            (target_logo_w, target_logo_h), Image.Resampling.LANCZOS
        )
        alpha = logo.getchannel("A").point(lambda value: int(value * OPACITY / 255))
        logo.putalpha(alpha)
        logo_w, logo_h = logo.size

    # Saat logo tersedia, ukuran teks dibuat sekitar 90% tinggi logo agar
    # tampak satu tingkat lebih kecil. Jika logo tidak ada, gunakan ukuran cadangan.
    font_size = max(1, int(logo_h * TEXT_TO_LOGO_HEIGHT_RATIO)) if logo else TEXT_SIZE
    font = load_font(font_size)
    text_bbox = font.getbbox(TEKS_WATERMARK)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # Logo berada tepat di atas tulisan; kelompok tetap di tengah bawah.
