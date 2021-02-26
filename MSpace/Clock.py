# importing required librarie 
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer, QTime, Qt


class ClockWidget(QWidget):

    def __init__(self):
        super().__init__()

        # setting geometry of main window 
        self.setGeometry(100, 100, 800, 400)

        # creating a vertical layout 
        layout = QVBoxLayout()

        # creating font object 
        font = QFont('Arial', 48, QFont.Bold)

        # creating a label object 
        self.label = QLabel()

        # setting centre alignment to the label 
        self.label.setAlignment(Qt.AlignCenter)

        # setting font to the label 
        self.label.setFont(font)

        # adding label to the layout 
        layout.addWidget(self.label)

        # setting the layout to main window 
        self.setLayout(layout)

        # creating a timer object 
        timer = QTimer(self)

        # adding action to timer 
        timer.timeout.connect(self.show_time)

        # update the timer every second 
        timer.start(1000)

        # method called by timer

    def show_time(self):
        # getting current time
        current_time = QTime.currentTime()

        # converting QTime object to string 
        label_time = current_time.toString('hh:mm:ss')

        # showing it to the label 
        self.label.setText(label_time) 