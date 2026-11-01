from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

class MLWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Machine Learning")
        self.resize(700, 450)
        layout = QVBoxLayout(self)
        label = QLabel("Machine Learning\n\nComing soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 22px; color: gray;")
        layout.addWidget(label)