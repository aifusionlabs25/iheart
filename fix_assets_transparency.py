from PyQt6.QtGui import QImage, QColor
import os

RESOURCES_DIR = r"c:\AI Fusion Labs\AI folder from OG Comp\iheart_dev\resources"

def make_transparent(filename):
    path = os.path.join(RESOURCES_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    img = QImage(path)
    img = img.convertToFormat(QImage.Format.Format_ARGB32)
    
    width = img.width()
    height = img.height()
    
    print(f"Processing {filename} ({width}x{height})...")
    
    for y in range(height):
        for x in range(width):
            pixel_color = img.pixelColor(x, y)
            # Check if pixel is white or near white
            if pixel_color.red() > 240 and pixel_color.green() > 240 and pixel_color.blue() > 240:
                # Set alpha to 0
                img.setPixelColor(x, y, QColor(0, 0, 0, 0))
                
    img.save(path)
    print(f"Saved transparency fix for {filename}")

files_to_fix = [
    "ui_switch_toggle_off.png",
    "ui_switch_toggle_on.png",
    "ui_gauge_vu.png"
]

for f in files_to_fix:
    make_transparent(f)
