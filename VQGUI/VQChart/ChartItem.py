from abc import abstractmethod
from typing import Tuple, Dict

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QRectF, Signal, QPointF
from PySide6.QtGui import QPen, QBrush, QFont, QColor
from PySide6.QtWidgets import QGraphicsTextItem
from pyqtgraph import InfiniteLine

from VQGUI.VQChart.Params import WHITE_COLOR, CURSOR_COLOR, BLACK_COLOR, NORMAL_FONT, BOTTOM_AXIS_FONT, RIGHT_AXIS_FONT, \
    GREY_COLOR, VPVR_COLOR, UnitVPVR_COLOR, POC_COLOR, VPVR_FONT, PRICE_LABEL_FONT, PRICE_LABEL_COLOR
from VQGUI.VQChart.TimeAxis import TimeAxis


class LineItem(pg.PlotCurveItem):
    def __init__(self, name=None, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setFlag(self.ItemUsesExtendedStyleOption)
        self.set_name(name)

    def set_name(self, name):
        self.opts['name'] = name

    def get_name(self):
        return self.name()

    def get_yrange(self, x_start, x_end):
        xdata, ydata = self.getData()
        idx = np.where((xdata >= x_start) & (xdata <= x_end))[0]

        if len(idx) > 0:
            ydata_selected = ydata[idx]
            y_start, y_end = np.min(ydata_selected), np.max(ydata_selected)
            return y_start, y_end
        else:
            return None, None

    def update_data(self, x, y):
        ori_xdata, ori_ydata = self.getData()
        if len(x) != len(ori_xdata):
            self.setData(x=x, y=y)
        elif (x != ori_xdata).any() or (y != ori_ydata).any():
            self.setData(x=x, y=y)


class VPVRItem(pg.GraphicsObject):

    def __init__(self, name=None, **opts):
        super().__init__()
        self._name = name
        self.picture = None
        self.text_picture = None
        self._text_shape = None
        self._shape = None
        self.setFlag(self.ItemUsesExtendedStyleOption)
        self._view_range = None
        self._price = None
        self._volume = None
        self._x_start = None
        self._x_end = None
        self.height = None
        self._opts = opts

    def setData(self, price, volume, view_range, x_start, x_end):
        self._price = price
        self._volume = volume
        self._view_range = view_range
        if x_start is None:
            self._x_start = view_range[0][0]
            self._x_end = view_range[0][1]
        else:
            self._x_start = x_start
            self._x_end = x_end
        self.draw()
        self.update()

    def setXrange(self, view_range, x_start=None, x_end=None):
        self._view_range = view_range
        if x_start is not None:
            self._x_start = x_start
            self._x_end = x_end
        if not (self._x_start > self._view_range[0][1] or self._x_end < self._view_range[0][0]):
            self.draw()
            self.update()

    def update_data(self, price, volume, view_range, x_start=None, x_end=None):
        if x_start is None:
            x_start = self._x_start
        if x_end is None:
            x_end = self._x_end

        if len(price) != len(self._price):
            self.setData(price, volume, view_range, x_start, x_end)
        elif (volume != self._volume).any() or (price != self._price).any():
            self.setData(price, volume, view_range, x_start, x_end)

    def draw(self):

        ymin, ymax = self._view_range[1][0], self._view_range[1][1]
        self.picture = QtGui.QPicture()
        self._shape = QtGui.QPainterPath()
        p = QtGui.QPainter(self.picture)

        if len(self._price) == 0:
            return
        elif len(self._price) == 1:
            last_price = self._price[0]
            if last_price <= 20:
                height = 0.01
            elif last_price <= 200:
                height = last_price // 20 * 0.01
            elif last_price <= 2000:
                height = last_price // 200 * 0.1
            else:
                height = last_price // 2000 * 1.0
        else:
            height = self._price[1] - self._price[0]
        top = self._price - height * 0.25
        self.height = height
        width = self._volume / np.max(self._volume) * (self._x_end - self._x_start) * 0.95

        if self._opts['color'] is None:
            pen = pg.mkPen(GREY_COLOR)
            brush = pg.mkBrush(GREY_COLOR)
        else:
            pen = pg.mkPen(self._opts['color'])
            brush = pg.mkBrush(self._opts['color'])
        h = height * 0.5
        poc_index = np.argmax(self._volume)
        p.setPen(pen)
        p.setBrush(brush)
        for i in range(len(self._price)):
            if ymin > self._price[i] or self._price[i] > ymax:
                continue
            # (x,y,w,h) (x,y)为坐标原点 w为横向宽度（x轴正方向），h为纵向宽度（y轴正方向）
            rect = QtCore.QRectF(self._x_start, top[i], width[i], h)
            if i == poc_index:
                p.setPen(pg.mkPen(POC_COLOR))
                p.setBrush(pg.mkBrush(POC_COLOR))
                p.drawRect(rect)
                self._shape.addRect(rect)
                p.setPen(pen)
                p.setBrush(brush)
            else:
                p.drawRect(rect)
                self._shape.addRect(rect)
        # bounding_rect = self.boundingRect()
        # print(bounding_rect, self.mapRectToDevice(bounding_rect))
        self.picture.play(p)
        p.end()
        # self.prepareGeometryChange()

    def paint(self, p, *args):
        if self.picture is None:
            self.draw()

        # if self.text_picture is None:
        #     self.draw_text()
        self.picture.play(p)
        # self.text_picture.play(p)

    # def draw_text(self):
    #     ymin, ymax = self._view_range[1][0], self._view_range[1][1]
    #     self.text_picture = QtGui.QPicture()
    #     self._text_shape = QtGui.QPainterPath()
    #     p = QtGui.QPainter(self.text_picture)
    #
    #     if len(self._price) == 0:
    #         return
    #     elif len(self._price) == 1:
    #         last_price = self._price[0]
    #         if last_price <= 20:
    #             height = 0.01
    #         elif last_price <= 200:
    #             height = last_price // 20 * 0.01
    #         elif last_price <= 2000:
    #             height = last_price // 200 * 0.1
    #         else:
    #             height = last_price // 2000 * 1.0
    #     else:
    #         height = self._price[1] - self._price[0]
    #
    #     top = self._price + height * 0.25
    #
    #     for i in range(len(self._price)):
    #         if ymin > self._price[i] or self._price[i] > ymax:
    #             continue
    #         text = QtGui.QStaticText(str(round(self._volume[i])))
    #         p.drawStaticText(QPointF(self.x_start, top[i]), text)
    #         self._text_shape.addText(QPointF(self.x_start, top[i]),font, str(round(self._volume[i])))
    #     p.end()
    #     # self.prepareGeometryChange()
    #     print(self.text_picture)
    # self.text_picture.play(p)

    def implements(self, interface=None):
        ints = ['plotData']
        if interface is None:
            return ints
        return interface in ints

    def boundingRect(self):
        if self.picture is None:
            self.draw()
        return QtCore.QRectF(self.picture.boundingRect())

    def shape(self):
        if self.picture is None:
            self.draw()
        return self._shape

    def name(self):
        return self._name

    def get_data(self):
        return self._price, self._volume

    def get_x_start(self):
        return self._x_start


class VPVRTextItem(pg.GraphicsObject):
    def __init__(self, parent: VPVRItem, *args):
        super().__init__(*args)
        self.vpvr = parent
        self.anchor = (0, 0)
        self.textItem_list = []

    def draw_text(self):
        price, volume = self.vpvr.get_data()
        top = price - self.vpvr.height * 0.25
        x = self.vpvr.get_x_start()
        for y, vol in zip(top, volume):
            textitem = QGraphicsTextItem()
            textitem.setParentItem(self.vpvr)
            font = VPVR_FONT
            textitem.setFont(font)
            textitem.setDefaultTextColor('w')
            textitem.setPos(QPointF(x, y))
            textitem.setPlainText(str(round(vol)))
            self.textItem_list.append(textitem)
        s = self.vpvr.scene()
        for item in self.textItem_list:
            s.addItem(item)

    def update_text(self):
        if self.textItem_list:
            pass
        else:
            self.draw_text()

    def paint(self, p, *args):
        pass
        # s.sigPrepareForPaint.connect(self.updateTransfrom)
        # self.updateTransform()
        # p.setTransform(self.sceneTransform())


class DrawLineItem(pg.InfiniteLine):
    def __init__(self):
        super().__init__()


class PriceLabelItem(pg.InfiniteLine):
    def __init__(self):
        labelOpts = {'position': 1.0, 'anchors': [(1, 1), (1, 1)], 'fill': PRICE_LABEL_COLOR, 'color': WHITE_COLOR}
        super().__init__(pos=0, angle=0, movable=False, label='{value:.2f}', labelOpts=labelOpts)

        pen = pg.mkPen(WHITE_COLOR, style=QtCore.Qt.DashLine)
        font = PRICE_LABEL_FONT
        # self.label.setZValue(100)
        self.label.setFont(font)
        self.setPen(pen)

    def setData(self, price):
        self.setValue(price)

    def update_data(self, price):
        self.setValue(price)


class Cursor(QtCore.QObject):
    """"""
    x_pos: Signal = Signal(int)

    def __init__(self, widget: pg.PlotWidget):
        """"""
        super().__init__()

        self._widget: pg.PlotWidget = widget

        self._x: int = 0
        self._y: float = 0

        self._v_lines: Dict[str, pg.InfiniteLine] = {}
        self._h_lines: Dict[str, pg.InfiniteLine] = {}
        self._views: Dict[str, pg.ViewBox] = {}
        self._now_plot_name: str = ""

        self._y_labels: Dict[str, pg.TextItem] = {}

        self._time_label = None
        self._price_label = None

    def init(self) -> None:
        """"""
        self.init_cursor()
        self.init_label()
        # self._init_label()
        # self._init_info()
        self._connect_signal()

    def init_label(self):
        if self._widget.scene() is not None:
            time_textitem = pg.TextItem("datetime", fill=CURSOR_COLOR, color=BLACK_COLOR, anchor=(0.5, 0))
            price_textitem = pg.TextItem("price", fill=CURSOR_COLOR, color=BLACK_COLOR, anchor=(0, 1))
            self._time_label: pg.TextItem = time_textitem
            self._time_label.setZValue(2)
            self._time_label.setFont(BOTTOM_AXIS_FONT)
            self._price_label: pg.TextItem = price_textitem
            self._price_label.setZValue(2)
            self._price_label.setFont(RIGHT_AXIS_FONT)
            self._time_label.hide()
            self._price_label.hide()
            self._widget.scene().addItem(self._time_label)
            self._widget.scene().addItem(self._price_label)
        # self._widget.get_plots()['MainChart'].getAxis('bottom').add_textitem(text_item)

    def init_cursor(self) -> None:
        """
        Create line objects.
        """

        pen = pg.mkPen(WHITE_COLOR)

        for plot_name, plot in self._widget.get_plots().items():
            if plot_name not in self._views.keys():
                v_line: pg.InfiniteLine = pg.InfiniteLine(angle=90, movable=False, pen=pen)
                h_line: pg.InfiniteLine = pg.InfiniteLine(angle=0, movable=False, pen=pen)
                view: pg.ViewBox = plot.getViewBox()

                for line in [v_line, h_line]:
                    line.setZValue(10)
                    line.hide()
                    view.addItem(line)

                self._v_lines[plot_name] = v_line
                self._h_lines[plot_name] = h_line
                self._views[plot_name] = view

    def _connect_signal(self) -> None:
        """
        Connect mouse move signal to update function.
        """
        # self.proxy = pg.SignalProxy(self._widget.scene().sigMouseMoved, rateLimit=60, slot=self._mouse_moved)
        self._widget.scene().sigMouseMoved.connect(self._mouse_moved)

    def _mouse_moved(self, evt) -> None:
        """
        Callback function when mouse is moved.
        """

        # First get current mouse point
        # pos = evt[0]
        pos = evt
        flag = False
        for plot_name, view in self._views.items():
            rect = view.sceneBoundingRect()
            if rect.contains(pos):
                mouse_point = view.mapSceneToView(pos)
                self._x = round(mouse_point.x())
                self._y = mouse_point.y()
                self._now_plot_name = plot_name
                flag = True
                break

        # Then update cursor component
        if flag:
            self._update_line()
            main_rect: QRectF = self._widget.main_chart.getViewBox().sceneBoundingRect()
            self._update_label(pos, main_rect)
            self.x_pos.emit(self._x)
        else:
            for line in list(self._v_lines.values()) + list(self._h_lines.values()):
                line.hide()
            self._time_label.hide()
            self._price_label.hide()

    def _update_line(self) -> None:
        """"""
        for v_line in self._v_lines.values():
            v_line.setPos(self._x)
            v_line.show()

        for plot_name, h_line in self._h_lines.items():
            if plot_name == self._now_plot_name:
                h_line.setPos(self._y)
                h_line.show()
            else:
                h_line.hide()

    def _update_label(self, mouse_pos, main_rect) -> None:
        self._time_label.setPos(mouse_pos.x(), main_rect.bottom())
        time_str: str = self._widget.main_chart.getAxis('bottom').get_tickstring(self._x)
        if '\n' in time_str:
            time_str = time_str[:11] + '     ' + time_str[11:]
        self._time_label.setText(time_str)
        self._time_label.show()
        self._price_label.setPos(main_rect.right(), mouse_pos.y())
        price_str = '{:.2f}'.format(round(self._y, 2))
        self._price_label.setText(price_str)
        self._price_label.show()

    #
    # def update_info(self) -> None:
    #     """"""
    #     buf: dict = {}
    #
    #     for item, plot in self._item_plot_map.items():
    #         item_info_text: str = item.get_info_text(self._x)
    #
    #         if plot not in buf:
    #             buf[plot] = item_info_text
    #         else:
    #             if item_info_text:
    #                 buf[plot] += ("\n\n" + item_info_text)
    #
    #     for plot_name, plot in self._plots.items():
    #         plot_info_text: str = buf[plot]
    #         info: pg.TextItem = self._infos[plot_name]
    #         info.setText(plot_info_text)
    #         info.show()
    #
    #         view: pg.ViewBox = self._views[plot_name]
    #         top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft())
    #         info.setPos(top_left)
    #
    # def move_right(self) -> None:
    #     """
    #     Move cursor index to right by 1.
    #     """
    #     if self._x == self._manager.get_count() - 1:
    #         return
    #     self._x += 1
    #
    #     self._update_after_move()
    #
    # def move_left(self) -> None:
    #     """
    #     Move cursor index to left by 1.
    #     """
    #     if self._x == 0:
    #         return
    #     self._x -= 1
    #
    #     self._update_after_move()
    #
    # def _update_after_move(self) -> None:
    #     """
    #     Update cursor after moved by left/right.
    #     """
    #     bar: BarData = self._manager.get_bar(self._x)
    #     self._y = bar.close_price
    #
    #     self._update_line()
    #     self._update_label()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._x = 0
        self._y = 0

        for line in list(self._v_lines.values()) + list(self._h_lines.values()):
            line.hide()
