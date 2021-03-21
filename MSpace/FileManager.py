from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QWidget
# Subclass QWiget to customize your application's main window


class OpenFile(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()

    def getfile(self, file_type: str):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file',
                                               'c:\\', file_type)
        return fname
