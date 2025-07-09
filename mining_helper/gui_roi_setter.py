import sys
import json
import threading
from detector import Detector
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QRect, Qt, QPoint
from PyQt5.QtGui import QPainter, QColor


CONFIG_FILE = "roi_config.json"
HANDLE_SIZE = 10


class Overlay(QWidget):
    def __init__(self, roi: QRect, update_callback=None):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        self.roi = QRect(roi)
        self.dragging = False
        self.resizing = False
        self.offset = QPoint()
        self.update_callback = update_callback

        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(255, 0, 0))
        painter.setBrush(Qt.transparent)
        painter.drawRect(self.roi)

        for dx in (0, self.roi.width()):
            for dy in (0, self.roi.height()):
                handle_center = QPoint(self.roi.x() + dx, self.roi.y() + dy)
                handle = QRect(handle_center.x() - HANDLE_SIZE//2, handle_center.y() - HANDLE_SIZE//2, HANDLE_SIZE, HANDLE_SIZE)
                painter.fillRect(handle, QColor(255, 0, 0))

    def mousePressEvent(self, event):
        if self._on_corner(event.pos()):
            self.resizing = True
            self.offset = event.pos()
        elif self.roi.contains(event.pos()):
            self.dragging = True
            self.offset = event.pos() - self.roi.topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.roi.moveTo(event.pos() - self.offset)
            self.update()
        elif self.resizing:
            diff = event.pos() - self.offset
            self.roi.setWidth(max(10, self.roi.width() + diff.x()))
            self.roi.setHeight(max(10, self.roi.height() + diff.y()))
            self.offset = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        if self.update_callback:
            self.update_callback(self.roi)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def _on_corner(self, pos):
        corner = QPoint(self.roi.right(), self.roi.bottom())
        return QRect(corner.x() - HANDLE_SIZE, corner.y() - HANDLE_SIZE, HANDLE_SIZE*2, HANDLE_SIZE*2).contains(pos)


class ROISetter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mining Assist - ROI Setter")
        self.setGeometry(300, 300, 600, 200)

        self.detector = None
        self.detector_thread = None
        
        self.overlay = None
        self.roi = self.load_roi()
        self.init_ui()
        self.show()

    def init_ui(self):
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                color: #333;
                font-family: Consolas;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.setter_button = QPushButton("Setter Mode")
        self.save_button = QPushButton("Save ROI")

        self.stop_button.setEnabled(False)

        for btn in [self.start_button, self.stop_button, self.setter_button, self.save_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #aaa;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)

        self.start_button.clicked.connect(self.start_detector)
        self.stop_button.clicked.connect(self.stop_detector)

        self.setter_button.clicked.connect(self.toggle_setter_mode)
        self.save_button.clicked.connect(self.save_roi)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.setter_button)
        button_layout.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.console)

        self.setLayout(layout)

    def start_detector(self):
        if self.detector:
            self.log("Detector is already running.")
            return

        self.detector = Detector(log_func=self.log)
        self.detector_thread = threading.Thread(target=self.detector.run_forever, daemon=True)
        self.detector_thread.start()
        self.log("Detector started.")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_detector(self):
        if self.detector:
            self.detector.stop()
            self.detector = None
            self.detector_thread = None
            self.log("Detector stopped.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def toggle_setter_mode(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.log("Setter mode OFF.")
        else:
            self.overlay = Overlay(self.roi, update_callback=self.on_roi_update)
            self.log("Setter mode ON.")

    def on_roi_update(self, new_roi):
        self.roi = QRect(new_roi)
        self.log(f"ROI updated to: {self.roi.x()}, {self.roi.y()}, {self.roi.width()}x{self.roi.height()}")

    def save_roi(self):
        roi_data = {
            "x": self.roi.x(),
            "y": self.roi.y(),
            "width": self.roi.width(),
            "height": self.roi.height()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(roi_data, f)
        self.log(f"ROI saved: {roi_data}")

    def load_roi(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return QRect(data["x"], data["y"], data["width"], data["height"])
        except:
            return QRect(500, 500, 200, 50)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")
        print(f"[LOG] {message}")

    def closeEvent(self, event):
        if self.overlay:
            self.overlay.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ROISetter()
    sys.exit(app.exec_())
