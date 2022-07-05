import pyqtgraph as pg
from PySide6 import QtWidgets, QtGui

from VQGUI.VQChart import MainChart
from VQGUI.VQChart.Params import GREY_COLOR, CURSOR_COLOR, BLACK_COLOR, NORMAL_FONT, RIGHT_AXIS_FONT, BOTTOM_AXIS_FONT
from VQGUI.VQChart.ChartItem import Cursor
from VisionQuant.utils.Params import Freq


class ChartWidget(pg.PlotWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._layout: pg.GraphicsLayout = pg.GraphicsLayout()
        self._layout.setSpacing(0)
        # self._layout.setBorder(color=GREY_COLOR, width=0.8)
        self._plots = dict()
        self.setCentralItem(self._layout)
        self._cursor = Cursor(self)
        self.main_chart: MainChart = MainChart()
        self._plots['main'] = self.main_chart
        self._layout.addItem(self.main_chart)
        self._layout.nextRow()
        self.analyze_result = None
        self.code = None

    def init(self, code, time_list, freq: Freq):
        self.code = code
        self.main_chart.init(time_list, freq)
        self._cursor.init()

    def add_plot(self, plot_name, plot: pg.PlotItem):
        self._plots[plot_name] = plot
        plot.setXLink(self.main_chart)
        plot.setMaximumHeight(150)
        self._layout.addItem(plot)
        self._layout.nextRow()
        self._cursor.init()

    def get_plots(self):
        return self._plots

    def get_plot(self, name):
        if name not in self._plots.keys():
            return None

        return self._plots[name]

    def get_cursor(self):
        return self._cursor

    def clear_plots(self):
        for plot in self._plots.values():
            plot.clear_plot()

    def clear_plot(self, plot_name):
        plot = self._plots[plot_name]
        plot.clear_plot()

    def show_plots(self, show_data_list: list):
        for update_data in show_data_list:
            plot_name = update_data['plot_name']
            data = update_data['data']
            plot = self.get_plot(plot_name)
            plot.show_plot(data)

    def update_plots(self, update_data_list: list):
        for update_data in update_data_list:
            plot_name = update_data['plot_name']
            data = update_data['data']
            plot = self.get_plot(plot_name)
            plot.update_plot(data)
