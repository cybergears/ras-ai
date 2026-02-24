import sys
from PyQt6.QtWidgets import QApplication
from ras_ui.hardcore_window import HardcoreWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HardcoreWindow()
    window.show()
    sys.exit(app.exec())