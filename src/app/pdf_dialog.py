import pandas as pd
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

import storage

def session_label(session_type, session_number):
    if pd.isna(session_number):
        return str(session_type)
    return f"{session_type}{int(session_number)}"

def document_label(key):
    return key.replace("_", " ").title()

class PdfDialog(QDialog):
    def __init__(self, year, category, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Documents - {category} {year}")
        self.resize(1100, 820)

        docs = pd.read_csv(storage.documents_path(year))
        docs = docs[docs["category"] == category].copy()
        docs["session_label"] = [
            session_label(t, n) for t, n in zip(docs["session_type"], docs["session_number"])
        ]
        self.docs = docs.sort_values("date")

        layout = QVBoxLayout(self)
        selectors = QHBoxLayout()
        self.event_combo = QComboBox()
        self.session_combo = QComboBox()
        self.document_combo = QComboBox()
        self.show_button = QPushButton("Show")
        self.browser_button = QPushButton("Open in browser")
        for label, widget in (("Event", self.event_combo), ("Session", self.session_combo),
                              ("Document", self.document_combo)):
            selectors.addWidget(QLabel(label))
            selectors.addWidget(widget, 1)
        selectors.addWidget(self.show_button)
        selectors.addWidget(self.browser_button)
        layout.addLayout(selectors)

        self.view = self._create_view()
        if self.view is not None:
            layout.addWidget(self.view, 1)
        else:
            self.show_button.setEnabled(False)
            layout.addWidget(QLabel("The embedded viewer is not available: use 'Open in browser'."), 1)
        layout.addWidget(QLabel("If nothing appears in the viewer, use 'Open in browser'."))

        self.event_combo.currentIndexChanged.connect(self._fill_sessions)
        self.session_combo.currentIndexChanged.connect(self._fill_documents)
        self.show_button.clicked.connect(self.show_document)
        self.browser_button.clicked.connect(self.open_in_browser)

        if self.docs.empty:
            self.show_button.setEnabled(False)
            self.browser_button.setEnabled(False)
            layout.addWidget(QLabel(f"No documents for {category} {year}."))
            return
        for _, row in self.docs.drop_duplicates("event").iterrows():
            self.event_combo.addItem(str(row["event_name"]).title(), row["event"])

    def _create_view(self):
        try:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            return None
        view = QWebEngineView()
        view.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        view.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        return view

    def _fill_sessions(self):
        self.session_combo.clear()
        subset = self.docs[self.docs["event"] == self.event_combo.currentData()]
        for label in subset["session_label"].drop_duplicates():
            self.session_combo.addItem(label, label)

    def _fill_documents(self):
        self.document_combo.clear()
        subset = self.docs[
            (self.docs["event"] == self.event_combo.currentData())
            & (self.docs["session_label"] == self.session_combo.currentData())
        ]
        ordered = sorted(subset.itertuples(), key=lambda r: (r.document != "classification", r.document))
        for row in ordered:
            self.document_combo.addItem(document_label(row.document), row.url)

    def show_document(self):
        url = self.document_combo.currentData()
        if url and self.view is not None:
            self.view.load(QUrl(url))

    def open_in_browser(self):
        url = self.document_combo.currentData()
        if url:
            QDesktopServices.openUrl(QUrl(url))