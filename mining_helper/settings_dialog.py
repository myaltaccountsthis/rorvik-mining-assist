from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QSpinBox,
    QPushButton, QFormLayout, QMessageBox
)
from config_manager import load_settings, save_settings, reset_settings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)

        self.current_settings = load_settings()

        self.fields = {}  # Hold references to spinboxes
        layout = QVBoxLayout()
        form = QFormLayout()

        # Add each editable value
        self.add_spin(form, "DEFAULT_DELAY", 0.0, 1.0, 0.01)
        self.add_spin(form, "POLL_INTERVAL", 0.0, 1.0, 0.001)
        self.add_spin(form, "RELEASE_DELAY", 0.0, 1.0, 0.01)
        self.add_spin(form, "RESET_TIMEOUT", 0.1, 10.0, 0.1)
        self.add_spin(form, "RECHECK_GRACE_PERIOD", 0.0, 1.0, 0.01)
        self.add_spin(form, "MAX_REENGAGE_ATTEMPTS", 1, 10, 1, integer=True)
        self.add_spin(form, "DOT_GRAY", 0, 255, 1, integer=True)
        self.add_spin(form, "FILL_GRAY", 0, 255, 1, integer=True)
        self.add_spin(form, "CRITICAL_GRAY", 0, 255, 1, integer=True)
        self.add_spin(form, "TOLERANCE", 0, 100, 1, integer=True)

        layout.addLayout(form)

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Reset to Defaults")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save)
        reset_btn.clicked.connect(self.reset)
        cancel_btn.clicked.connect(self.reject)

        btns.addWidget(save_btn)
        btns.addWidget(reset_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        self.setLayout(layout)

    def add_spin(self, layout, key, min_val, max_val, step, integer=False):
        if integer:
            field = QSpinBox()
        else:
            field = QDoubleSpinBox()
            field.setDecimals(3)
        field.setMinimum(min_val)
        field.setMaximum(max_val)
        field.setSingleStep(step)
        field.setValue(self.current_settings.get(key, 0))
        self.fields[key] = field
        layout.addRow(QLabel(key), field)

    def save(self):
        new_settings = {key: field.value() for key, field in self.fields.items()}
        save_settings(new_settings)
        QMessageBox.information(self, "Settings Saved", "Settings were saved successfully.")
        self.accept()

    def reset(self):
        from constants import DEFAULT_SETTINGS
        for key, val in DEFAULT_SETTINGS.items():
            if key in self.fields:
                self.fields[key].setValue(val)
        save_settings(DEFAULT_SETTINGS)
        QMessageBox.information(self, "Settings Reset", "Settings reset to default.")
