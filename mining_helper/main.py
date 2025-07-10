import sys
from PyQt5.QtWidgets import QApplication
from gui_roi_setter import ROISetter

def main():
    app = QApplication(sys.argv)
    window = ROISetter()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
