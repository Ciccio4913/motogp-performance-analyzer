import os
import sys
from pathlib import Path

os.environ.setdefault("QT_API", "pyside6")

SRC = Path(__file__).resolve().parents[1]
sys.path.append(str(SRC / "visualization"))
sys.path.append(str(SRC / "ml"))

from PySide6.QtWidgets import QApplication

from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
