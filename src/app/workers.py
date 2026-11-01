import threading

from PySide6.QtCore import QThread, Signal

class TaskWorker(QThread):
    progress = Signal(int, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self._task = task
        self._cancel = threading.Event()
        self.result = None
        self.error = None

    def cancel(self):
        self._cancel.set()

    def run(self):
        try:
            self.result = self._task(progress=self.progress.emit, cancel=self._cancel)
        except Exception as exc:
            self.error = str(exc)