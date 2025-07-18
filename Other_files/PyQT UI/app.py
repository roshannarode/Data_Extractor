import sys
from PyQt5.QtWidgets import QApplication
from gui import CSVSummaryApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVSummaryApp()
    window.show()
    sys.exit(app.exec_())
