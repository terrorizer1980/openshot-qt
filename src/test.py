from PyQt5.QtWidgets import QWidget, QApplication
app = QApplication([])
from windows.exportClips import clipExportWindow
exp = clipExportWindow()
exp.exec_()
