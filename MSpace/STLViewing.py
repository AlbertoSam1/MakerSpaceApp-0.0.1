from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot
import sys

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

pyplot.style.use('classic')


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        # Create a new plot
        figure = pyplot.figure()
        axes = mplot3d.Axes3D(figure)
        axes._axis3don = False

        # Load the STL files and add the vectors to the plot
        your_mesh = mesh.Mesh.from_file('stl-test.STL')
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(your_mesh.vectors))

        # Auto scale to the mesh size
        scale = your_mesh.points.flatten('A')
        axes.auto_scale_xyz(scale, scale, scale)

        # Show the plot to the screen
        pyplot.show()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()