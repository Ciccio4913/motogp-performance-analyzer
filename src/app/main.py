import os
import sys
from pathlib import Path

os.environ.setdefault("QT_API", "pyside6")

sys.path.append(str(Path(__file__).resolve().parents[1] / "visualization"))

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