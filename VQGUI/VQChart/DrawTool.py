import pyqtgraph as pg
from PySide6 import QtCore
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
from VQGUI.VQChart.ChartItem import TrendLineItem


class DrawTool:
    def __init__(self, parent: pg.PlotItem):
        self.parent = parent
        self._view = self.parent.getViewBox()
        self._click_count = 0
        self._current_item = None
        self._tmp_data = None

    def connect_left_mouse_clicked_signal(self, callback):
        if self.parent.scene():
            self.parent.scene().sigMouseClicked.connect(callback)
        else:
            print("未初始化")

    def disconnect_left_mouse_clicked_signal(self, callback):
        if self.parent.scene():
            self.parent.scene().sigMouseClicked.disconnect(callback)
        else:
            print("未初始化")

    def connect_mouse_moved_signal(self, callback):
        if self.parent.scene():
            self.parent.scene().sigMouseMoved.connect(callback)
        else:
            print("未初始化")

    def disconnect_mouse_moved_signal(self, callback):
        if self.parent.scene():
            self.parent.scene().sigMouseMoved.disconnect(callback)
        else:
            print("未初始化")

    def mouse_clicked(self, ev):
        print(ev)
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            true_pos = self._view.mapSceneToView(ev.pos())
            print(true_pos.x(), true_pos.y())

    def draw_trend_line(self):
        self._current_item = TrendLineItem()
        self.connect_left_mouse_clicked_signal(self._draw_trend_line_mouse_clicked)
        self.connect_mouse_moved_signal(self._draw_trend_line_mouse_moved)
        self._current_item.sigRightButtonClicked.connect(self.remove_item)

    def _draw_trend_line_mouse_clicked(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._click_count == 0:
                self._current_item.set_start_pos(self._tmp_data)
                self.parent.add_draw_item(self._current_item, name=self._current_item.name())
                self._click_count += 1
            elif self._click_count == 1:
                self._current_item.set_end_pos(self._tmp_data)
                self.disconnect_mouse_moved_signal(self._draw_trend_line_mouse_moved)
                self.disconnect_left_mouse_clicked_signal(self._draw_trend_line_mouse_clicked)
                self._click_count = 0

    def _draw_trend_line_mouse_moved(self, ev):
        self._tmp_data = self._view.mapSceneToView(ev)
        self._current_item.set_end_pos(self._tmp_data)

    def remove_item(self, item_name: str):
        print("删除", item_name)
        self.parent.remove_item(item_name)
