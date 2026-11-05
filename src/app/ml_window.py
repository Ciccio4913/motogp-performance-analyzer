from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from workers import TaskWorker

CATEGORIES = ["MotoGP", "Moto2", "Moto3"]

SUMMARY_COLUMNS = [
    ("mae_rank", "Error (positions)", "{:.2f}"),
    ("spearman", "Order correlation", "{:.2f}"),
    ("top3_hits", "Podium hits (of 3)", "{:.2f}"),
    ("top10_hits", "Top-10 hits (of 10)", "{:.1f}"),
    ("vs_grid_pct", "vs grid position", "{:+.1f}%"),
    ("races", "Races", "{:.0f}"),
]

def _fill_table(table, headers, rows):
    table.clear()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            if c > 0:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)

def _new_table():
    table = QTableWidget()
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.verticalHeader().setVisible(False)
    return table

def mae_chart(summary):
    fig = Figure(figsize=(6, 3.2), layout="tight")
    ax = fig.subplots()
    names = list(summary.index)
    values = list(summary["mae_rank"])
    colors = ["lightgray" if "baseline" in name else "tab:blue" for name in names]
    bars = ax.barh(names, values, color=colors, edgecolor="black")
    ax.bar_label(bars, fmt="%.2f")
    ax.invert_yaxis()
    ax.margins(x=0.12)
    ax.set_xlabel("Average error in finishing positions (lower is better)")
    return fig

class MLWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Machine Learning - finishing position prediction")
        self.resize(1100, 760)
        self.worker = None
        self._race_tables = {}
        self._canvas = None
        self._build_ui()
        self.on_category_changed()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Predicts each rider's finishing position from what is known before the start: "
            "practice, qualifying, sprint, warm-up and the previous season's results."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        top = QHBoxLayout()
        top.addWidget(QLabel("Category"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        top.addWidget(self.category_combo)
        self.train_button = QPushButton("Train and evaluate")
        self.train_button.clicked.connect(self.start_training)
        top.addWidget(self.train_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        top.addWidget(self.progress, 1)
        layout.addLayout(top)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_evaluation_tab(), "Evaluation")
        self.tabs.addTab(self._build_prediction_tab(), "Race prediction")

    def _build_evaluation_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.eval_info = QLabel("Press 'Train and evaluate' to compare the models with the baselines.")
        self.eval_info.setWordWrap(True)
        layout.addWidget(self.eval_info)
        self.summary_table = _new_table()
        layout.addWidget(self.summary_table)
        self.chart_box = QVBoxLayout()
        layout.addLayout(self.chart_box, 1)
        return page

    def _build_prediction_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        row.addWidget(QLabel("Season"))
        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(self.on_year_changed)
        row.addWidget(self.year_combo)
        row.addWidget(QLabel("Race"))
        self.event_combo = QComboBox()
        self.event_combo.setMinimumWidth(260)
        row.addWidget(self.event_combo, 1)
        self.predict_button = QPushButton("Predict")
        self.predict_button.clicked.connect(self.predict_clicked)
        row.addWidget(self.predict_button)
        layout.addLayout(row)
        self.predict_info = QLabel("")
        self.predict_info.setWordWrap(True)
        layout.addWidget(self.predict_info)
        self.predict_table = _new_table()
        layout.addWidget(self.predict_table, 1)
        return page

    def category(self):
        return self.category_combo.currentText()

    def on_category_changed(self):
        self._clear_chart()
        self.summary_table.clear()
        self.summary_table.setRowCount(0)
        self.predict_table.clear()
        self.predict_table.setRowCount(0)
        self.predict_info.setText("")
        self.eval_info.setText("Press 'Train and evaluate' to compare the models with the baselines.")
        try:
            import predict
        except ImportError as exc:
            self._missing_library(exc)
            return
        bundle = predict.load_bundle(self.category())
        if bundle is None:
            self.status.setText("No trained model for this category yet.")
        else:
            self.status.setText(
                f"A saved model is available ({bundle['model_name']}, trained on "
                f"{bundle['trained_years'][0]}-{bundle['trained_years'][-1]}). "
                "Press 'Train and evaluate' to refresh it."
            )
        self.refresh_prediction_controls()

    def _missing_library(self, exc):
        self.train_button.setEnabled(False)
        self.predict_button.setEnabled(False)
        self.status.setText(f"scikit-learn is not installed ({exc}). Run start.bat again to install it.")

    def start_training(self):
        try:
            import train
        except ImportError as exc:
            QMessageBox.critical(self, "Machine learning", f"A required library is missing: {exc}")
            return
        category = self.category()
        self.progress.setValue(0)
        self.set_busy(True)
        self.worker = TaskWorker(lambda progress, cancel: train.run_evaluation(category, progress))
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_training_finished)
        self.worker.start()

    def on_progress(self, percent, message):
        self.progress.setValue(percent)
        self.status.setText(message)

    def on_training_finished(self):
        worker, self.worker = self.worker, None
        self.set_busy(False)
        if worker.error:
            self.progress.setValue(0)
            self.status.setText(f"Error: {worker.error}")
            QMessageBox.critical(self, "Machine learning", worker.error)
        else:
            self.show_results(worker.result)
            self.status.setText(f"Done. Saved model: {worker.result['best_model']}")
            self.refresh_prediction_controls()
        worker.deleteLater()

    def set_busy(self, busy):
        for widget in (self.train_button, self.category_combo, self.predict_button):
            widget.setEnabled(not busy)

    def show_results(self, result):
        summary = result["summary"]
        rows = []
        for method, row in summary.iterrows():
            rows.append([method] + [fmt.format(row[col]) for col, _, fmt in SUMMARY_COLUMNS])
        _fill_table(self.summary_table, ["Method"] + [title for _, title, _ in SUMMARY_COLUMNS], rows)

        if result["test_year"] is not None:
            test_years = list(result["mae_by_year"].columns)
            how = (f"Walk-forward evaluation: each season from {test_years[0]} to {test_years[-1]} is "
                   f"predicted by models trained only on earlier seasons. The saved model "
                   f"({result['best_model']}) is trained on {result['trained_years'][0]}-"
                   f"{result['trained_years'][-1]}, so {result['test_year']} is out-of-sample.")
        else:
            how = ("Only one season is available: results come from cross-validation by race and are "
                   "indicative only. Download more seasons for a reliable evaluation.")
        self.eval_info.setText(
            f"{how}\nError = average difference between predicted and real finishing position among "
            "riders who finished. Baselines (gray) use no learning: grid position, or practice pace."
        )
        self._clear_chart()
        self._canvas = FigureCanvasQTAgg(mae_chart(summary))
        self.chart_box.addWidget(self._canvas)

    def _clear_chart(self):
        if self._canvas is not None:
            self.chart_box.removeWidget(self._canvas)
            self._canvas.setParent(None)
            self._canvas.deleteLater()
            self._canvas = None

    def race_table(self):
        import predict
        category = self.category()
        if category not in self._race_tables:
            self._race_tables[category] = predict.build_table(category)
        return self._race_tables[category]

    def refresh_prediction_controls(self):
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        try:
            table = self.race_table()
        except Exception:
            self.event_combo.clear()
            self.predict_button.setEnabled(False)
            self.year_combo.blockSignals(False)
            return
        for year in sorted(table["year"].unique(), reverse=True):
            self.year_combo.addItem(str(int(year)), int(year))
        self.year_combo.blockSignals(False)
        self.predict_button.setEnabled(True)
        self.on_year_changed()

    def on_year_changed(self):
        import predict
        self.event_combo.clear()
        year = self.year_combo.currentData()
        if year is None:
            return
        for code, label in predict.events_in_year(self.race_table(), year):
            self.event_combo.addItem(label, code)

    def predict_clicked(self):
        import predict
        bundle = predict.load_bundle(self.category())
        if bundle is None:
            QMessageBox.information(self, "Machine learning", "Train a model first: press 'Train and evaluate'.")
            return
        year, event = self.year_combo.currentData(), self.event_combo.currentData()
        if year is None or event is None:
            return
        race, metrics = predict.predict_event(self.race_table(), bundle, year, event)

        rows = []
        for _, r in race.iterrows():
            grid = "-" if r["grid_position"] != r["grid_position"] else int(r["grid_position"])
            actual = r["status"] if r["race_position"] != r["race_position"] else int(r["race_position"])
            rows.append([int(r["predicted_rank"]), r["rider_name"], r["constructor_name"], grid, actual])
        _fill_table(self.predict_table,
                    ["Predicted", "Rider", "Constructor", "Grid", "Actual finish"], rows)

        seen = bool(race["in_training"].iloc[0])
        origin = ("This season was part of the training data: the result is optimistic."
                  if seen else "Out-of-sample: the model has not seen this season.")
        if metrics is not None:
            origin += (f"  Error {metrics['mae_rank']:.2f} positions | order correlation "
                       f"{metrics['spearman']:.2f} | podium hits {metrics['top3_hits']}/3")
        self.predict_info.setText(origin)

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.wait(120000)
        event.accept()
