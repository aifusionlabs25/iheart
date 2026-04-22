import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor
from PyQt6.QtCore import Qt

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pinup Test")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: #383b40;") # Gunship Gray

        layout = QVBoxLayout(self)
        
        # Path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pinup_path = os.path.join(base_dir, 'assets', 'pinup.png')
        print(f"Testing Path: {pinup_path}")
        
        self.lbl = QLabel("Placeholder")
        layout.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(pinup_path):
            img = QImage(pinup_path)
            if img.isNull():
                print("ERROR: Image loaded but is null!")
                self.lbl.setText("Image Null")
                return

            print(f"Image Size: {img.width()}x{img.height()}")
            
            # Transparency Logic
            try:
                bg_color = img.pixelColor(0, 0)
                print(f"Top-Left Pixel Color: {bg_color.name()}")
                
                mask_img = img.createMaskFromColor(bg_color.rgb(), Qt.MaskMode.MaskOutColor)
                mask = QBitmap.fromImage(mask_img)
                
                pix = QPixmap.fromImage(img)
                pix.setMask(mask)
                
                # Scale
                pix = pix.scaled(260, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl.setPixmap(pix)
                print("Success: Pixmap set with mask.")
                
            except Exception as e:
                print(f"Exception during processing: {e}")
                self.lbl.setText(f"Error: {e}")
        else:
            print("ERROR: File not found!")
            self.lbl.setText("File Not Found")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
