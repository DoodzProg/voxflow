"""
create_icon.py

One-shot utility: renders assets/logo.svg into a multi-resolution
assets/icon.ico suitable for Windows application icons and PyInstaller.

Requires:
    pip install PySide6 Pillow

Usage:
    python create_icon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# PySide6 must be importable (used for high-quality SVG rasterisation).
# ---------------------------------------------------------------------------
try:
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication
except ImportError:
    sys.exit("PySide6 is required.  Run: pip install PySide6")

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required.  Run: pip install Pillow")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
SVG_PATH = ROOT / "assets" / "logo.svg"
ICO_PATH = ROOT / "assets" / "icon.ico"

# ICO standard sizes (must include at least 16, 32, 48, 256 for Windows)
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_svg(svg_bytes: bytes, size: int) -> Image.Image:
    """Render *svg_bytes* at *size* × *size* pixels via Qt.

    Args:
        svg_bytes: Raw SVG file content.
        size: Target square pixel size.

    Returns:
        A Pillow RGBA image.
    """
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)  # transparent
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    # Convert QImage → bytes → Pillow.
    # In recent PySide6 versions img.bits() returns a plain memoryview,
    # so bytes() conversion works directly without setsize().
    raw = bytes(img.bits())
    pil = Image.frombuffer("RGBA", (size, size), raw, "raw", "BGRA", 0, 1)
    return pil


def main() -> None:
    """Entry point: render SVG at all target sizes and write the .ico."""
    if not SVG_PATH.exists():
        sys.exit(f"SVG not found: {SVG_PATH}")

    # QApplication is required for QSvgRenderer.
    app = QApplication.instance() or QApplication(sys.argv)

    svg_bytes = SVG_PATH.read_bytes()
    frames: list[Image.Image] = []

    for size in SIZES:
        print(f"  Rendering {size}×{size}…")
        frames.append(render_svg(svg_bytes, size))

    # Save as multi-resolution ICO.
    frames[0].save(
        ICO_PATH,
        format="ICO",
        append_images=frames[1:],
        sizes=[(s, s) for s in SIZES],
    )
    print(f"\n✓  Written: {ICO_PATH}")


if __name__ == "__main__":
    main()
