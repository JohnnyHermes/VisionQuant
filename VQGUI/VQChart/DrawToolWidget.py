from PySide6 import QtCore

from .ui_DrawToolWidget import Ui_Form

from PySide6.QtWidgets import QWidget


class DrawToolWidget(QWidget):
    def __init__(self):
        super(DrawToolWidget, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._draw_tool = None

    def init(self, draw_tool):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self._draw_tool = draw_tool
        self.ui.TrendLine.clicked.connect(self._draw_tool.draw_trend_line)
