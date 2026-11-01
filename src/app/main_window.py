from datetime import date

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QStackedWidget, QTabWidget,
    QVBoxLayout, QWidget,
)

import collector
import processor
import storage
from charts import (
    available_categories, constructor_points_chart, load_season,
    retirements_chart, top_riders_chart,
)
from config import FIRST_SEASON
from ml_window import MLWindow
from pdf_dialog import PdfDialog
from workers import TaskWorker

PAGE_EMPTY, PAGE_CONVERT, PAGE_CHARTS = 0, 1, 2

class ChartTab(QWidget):
    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widgets = []

    def show_figure(self, figure):
        for widget in self._widgets:
            self._layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbar2QT(canvas, self)
        self._widgets = [toolbar, canvas]
        self._layout.addWidget(toolbar)
        self._layout.addWidget(canvas)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MotoGP Performance Analyzer")
        self.resize(1280, 780)
        self.worker = None
        self._on_success = None
        self._task_year = None
        self._df_cache = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        title = QLabel("MotoGP Performance Analyzer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; padding: 8px;")
        root.addWidget(title)

        body = QHBoxLayout()
        root.addLayout(body, 1)
        body.addWidget(self._build_left_column())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_empty_page())
        self.pages.addWidget(self._build_convert_page())
        self.pages.addWidget(self._build_charts_page())
        body.addWidget(self.pages, 1)

    def _build_left_column(self):
        column = QWidget()
        column.setFixedWidth(290)
        layout = QVBoxLayout(column)

        group = QGroupBox("Data")
        box = QVBoxLayout(group)
        box.addWidget(QLabel("Select a season based on its year"))
        self.year_combo = QComboBox()
        self.year_combo.setMaxVisibleItems(15)
        for year in range(date.today().year, FIRST_SEASON - 1, -1):
            self.year_combo.addItem(str(year), year)
        self.year_combo.currentIndexChanged.connect(self.on_year_changed)
        box.addWidget(self.year_combo)

        self.year_status = QLabel()
        self.year_status.setStyleSheet("color: gray;")
        box.addWidget(self.year_status)

        self.download_button = QPushButton("Download JSON")
        self.download_button.clicked.connect(self.on_download_clicked)
        box.addWidget(self.download_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        box.addWidget(self.progress)
        self.message = QLabel("")
        self.message.setWordWrap(True)
        box.addWidget(self.message)

        self.delete_json_button = QPushButton("Delete JSON")
        self.delete_json_button.clicked.connect(self.on_delete_json)
        box.addWidget(self.delete_json_button)

        layout.addWidget(group)
        layout.addStretch()
        self.ml_button = QPushButton("MACHINE LEARNING")
        self.ml_button.setMinimumHeight(44)
        self.ml_button.clicked.connect(self.on_ml_clicked)
        layout.addWidget(self.ml_button)
        return column

    def _build_empty_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("DOWNLOAD JSON\nTO START ANALYSIS")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: gray;")
        layout.addWidget(label)
        return page

    def _build_convert_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch()
        self.convert_label = QLabel()
        self.convert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.convert_label.setStyleSheet("font-size: 18px; color: gray;")
        layout.addWidget(self.convert_label)
        self.convert_button = QPushButton("Convert JSON to CSV")
        self.convert_button.setMinimumHeight(44)
        self.convert_button.setMaximumWidth(280)
        self.convert_button.clicked.connect(self.start_convert)
        layout.addWidget(self.convert_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    def _build_charts_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)

        side_widget = QWidget()
        side_widget.setFixedWidth(150)
        side = QVBoxLayout(side_widget)
        side.setContentsMargins(0, 0, 0, 0)
        side.addWidget(QLabel("Category"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.draw_charts)
        side.addWidget(self.category_combo)
        self.pdf_button = QPushButton("PDF")
        self.pdf_button.clicked.connect(self.on_pdf_clicked)
        side.addWidget(self.pdf_button)
        side.addStretch()
        self.delete_csv_button = QPushButton("Delete CSV")
        self.delete_csv_button.clicked.connect(self.on_delete_csv)
        side.addWidget(self.delete_csv_button)
        layout.addWidget(side_widget)

        self.tabs = QTabWidget()
        self.chart_tabs = [ChartTab() for _ in range(3)]
        for tab, name in zip(self.chart_tabs, ("Top riders", "Constructors", "Non-finishes")):
            self.tabs.addTab(tab, name)
        layout.addWidget(self.tabs, 1)
        return page

    def current_year(self):
        return self.year_combo.currentData()

    def refresh(self):
        year = self.current_year()
        raw_count = storage.raw_file_count(year)
        has_csv = storage.has_csv(year)
        json_text = f"{raw_count} files" if raw_count else "no"
        self.year_status.setText(f"JSON: {json_text}   |   CSV: {'yes' if has_csv else 'no'}")

        busy = self.worker is not None
        self.delete_json_button.setEnabled(not busy and bool(storage.deletable_raw_years()))
        self.delete_csv_button.setEnabled(not busy and bool(storage.years_with_csv()))

        if has_csv:
            try:
                self.show_charts(year)
                return
            except Exception as exc:
                self.message.setText(f"Could not read the CSV: {exc}")
        if raw_count:
            self.convert_label.setText(f"{raw_count} JSON files found for {year}")
            self.pages.setCurrentIndex(PAGE_CONVERT)
        else:
            self.pages.setCurrentIndex(PAGE_EMPTY)

    def set_busy(self, busy, cancellable=False):
        for widget in (self.year_combo, self.convert_button, self.pdf_button, self.category_combo):
            widget.setEnabled(not busy)
        if busy:
            self.delete_json_button.setEnabled(False)
            self.delete_csv_button.setEnabled(False)
        if busy and cancellable:
            self.download_button.setText("Cancel")
            self.download_button.setEnabled(True)
        else:
            self.download_button.setText("Download JSON")
            self.download_button.setEnabled(not busy)

    def on_year_changed(self):
        self.message.setText("")
        self.progress.setValue(0)
        self.refresh()

    def run_task(self, task, on_success, cancellable=False):
        self._task_year = self.current_year()
        self._on_success = on_success
        self.worker = TaskWorker(task)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_task_finished)
        self.set_busy(True, cancellable)
        self.worker.start()

    def on_progress(self, percent, message):
        self.progress.setValue(percent)
        self.message.setText(message)

    def on_task_finished(self):
        worker, self.worker = self.worker, None
        self.set_busy(False)
        if worker.error:
            self.progress.setValue(0)
            self.message.setText(f"Error: {worker.error}")
            QMessageBox.critical(self, "Error", worker.error)
        else:
            self._on_success(worker.result)
        self.refresh()
        worker.deleteLater()

    def on_download_clicked(self):
        if self.worker is not None:
            self.worker.cancel()
            self.download_button.setEnabled(False)
            self.message.setText("Cancelling...")
            return
        year = self.current_year()
        self.progress.setValue(0)
        self.run_task(
            lambda progress, cancel: collector.download_season(year, progress, cancel),
            self.after_download,
            cancellable=True,
        )

    def after_download(self, summary):
        text = f"{summary['downloaded']} new files, {summary['skipped']} already there"
        if summary["missing"]:
            text += f", {summary['missing']} not available"
        if summary["failed"]:
            text += f", {summary['failed']} FAILED: press Download again to retry"
        if summary["cancelled"]:
            text = "Cancelled. " + text
        self.message.setText(text)
        self._df_cache.pop(self._task_year, None)

        if (not summary["cancelled"] and not summary["failed"]
                and storage.has_csv(self._task_year) and storage.has_raw(self._task_year)):
            self.start_convert()

    def start_convert(self):
        year = self.current_year()
        self.progress.setValue(0)
        self.run_task(
            lambda progress, cancel: processor.convert_season(year, progress, cancel),
            self.after_convert,
        )

    def after_convert(self, result):
        self._df_cache.pop(self._task_year, None)
        text = f"CSV ready: {result['rows']} rows, {result['documents']} documents indexed"
        if result["bad_files"]:
            text += f" ({result['bad_files']} unreadable JSON skipped)"
        self.message.setText(text)

    def load_dataframe(self, year):
        if year not in self._df_cache:
            self._df_cache[year] = load_season(year)
        return self._df_cache[year]

    def show_charts(self, year):
        df = self.load_dataframe(year)
        categories = available_categories(df)
        previous = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(categories)
        if previous in categories:
            self.category_combo.setCurrentText(previous)
        self.category_combo.blockSignals(False)
        self.pages.setCurrentIndex(PAGE_CHARTS)
        self.draw_charts()

    def draw_charts(self):
        category = self.category_combo.currentText()
        if not category:
            return
        year = self.current_year()
        df = self.load_dataframe(year)
        figures = (
            top_riders_chart(df, category, year),
            constructor_points_chart(df, category, year),
            retirements_chart(df, category, year),
        )
        for tab, figure in zip(self.chart_tabs, figures):
            tab.show_figure(figure)

    def choose_years(self, title, years):
        items = ["All years"] + [str(year) for year in years]
        item, ok = QInputDialog.getItem(self, title, "Choose what to delete:", items, 0, False)
        if not ok:
            return None
        return list(years) if item == "All years" else [int(item)]

    def confirm(self, text):
        answer = QMessageBox.question(self, "Confirm", text)
        return answer == QMessageBox.StandardButton.Yes

    def on_delete_json(self):
        years = storage.deletable_raw_years()
        chosen = self.choose_years("Delete JSON", years)
        if not chosen or not self.confirm(f"Delete the JSON files of: {', '.join(map(str, chosen))}?"):
            return
        for year in chosen:
            storage.delete_raw(year)
        self.message.setText(f"JSON deleted: {', '.join(map(str, chosen))}")
        self.refresh()

    def on_delete_csv(self):
        years = storage.years_with_csv()
        chosen = self.choose_years("Delete CSV", years)
        if not chosen or not self.confirm(f"Delete the CSV of: {', '.join(map(str, chosen))}?"):
            return
        for year in chosen:
            storage.delete_csv(year)
            self._df_cache.pop(year, None)
        self.message.setText(f"CSV deleted: {', '.join(map(str, chosen))}")
        self.refresh()

    def on_pdf_clicked(self):
        year = self.current_year()
        if not storage.has_documents(year):
            QMessageBox.information(
                self, "Documents",
                "There is no document index for this season yet.\n\n"
                "Press 'Download JSON' again: it only fetches what is missing "
                "and refreshes the index.",
            )
            return
        PdfDialog(year, self.category_combo.currentText(), self).exec()

    def on_ml_clicked(self):
        MLWindow(self).exec()

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.cancel()
            self.worker.wait(20000)
        event.accept()