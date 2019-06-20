# -*- coding: utf-8 -*-
'''
This module provides a class for real-time plotting of results in a pop-up
graph window.

Call a graph in main GUI class like this:

self.press_graph = plotting.MakeGraph(title='Pressure',
                                          xlabel='Time (min)',
                                          ylabel='Pressure (Torr)')
self.press_graph.append(self.ops_dict['elapsed_time'],
                        self.vac_dict['current_pressure'])
self.press_graph.show()
'''

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
import pyqtgraph as pg


class MakeGraph(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None, title=None,
                 line_color=QColor(Qt.lightGray),
                 xmax=500, xlabel='X', ylabel='Y'):
        # color of plot line
        pen = QPen(line_color)
        # width of plot line
        pen.setWidth(0)

        super().__init__(parent)
        # sert title of plot window and add axis labels
        self.setWindowTitle(title)
        self.plot = self.addPlot(
                title=title, labels={'left': ylabel, 'bottom': xlabel})
        # self.plot.showAxis("bottom", False)
        self.curve = self.plot.plot(pen=pen)
        self.xs = []
        self.ys = []
        self.xmax = xmax

    def trim(self):
        self.curve.setData(self.xs[-self.xmax:], self.ys[-self.xmax:])

    def append(self, x, y):
        # append single point to graph and trim off points past xmax
        self.xs.append(x)
        self.ys.append(y)
        self.trim()

    def append_many(self, many):
        # append multiple points to graph in form [[x1,y1],[x2,y2],...]
        for m in many:
            self.xs.append(m[0])
            self.ys.append(m[1])
        self.trim()
