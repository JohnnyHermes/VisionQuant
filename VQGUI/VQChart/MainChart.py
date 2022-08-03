import math
from copy import deepcopy
import numpy as np
import pyqtgraph as pg
from PySide6 import QtGui
from pyqtgraph import BarGraphItem, InfiniteLine

from VQGUI.VQChart.Params import NORMAL_FONT, GREY_COLOR, WHITE_COLOR, CURSOR_COLOR, BLACK_COLOR, RIGHT_AXIS_FONT, \
    BOTTOM_AXIS_FONT, VPVR_COLOR, UnitVPVR_COLOR, VPVR_FONT
from VQGUI.VQChart.TimeAxis import TimeAxis
from VQGUI.VQChart.ChartItem import LineItem, VPVRItem, PriceLabelItem
from VisionQuant.utils.Code import Code
from VisionQuant.utils.Params import Freq


class MainChart(pg.PlotItem):
    def __init__(self, *args, **kargs):
        super().__init__(axisItems={'bottom': TimeAxis()}, *args, **kargs)
        self.setMenuEnabled(False)
        self.setClipToView(True)
        self.hideAxis('left')
        self.showAxis('right')
        self.setDownsampling(mode='peak')
        self.setLimits(xMin=-1, minXRange=-1)
        self.hideButtons()
        self.items_dict = dict()
        self.proxy = None

        # Connect view change signal to update y range function
        view: pg.ViewBox = self.getViewBox()
        view.setBorder(color=WHITE_COLOR, width=0.8)
        view.setMouseEnabled(x=True, y=False)
        view.disableAutoRange()

        # Set right axis
        right_axis: pg.AxisItem = self.getAxis('right')
        right_axis.setWidth(60)
        right_axis.setStyle(tickFont=RIGHT_AXIS_FONT)

        bottom_axis: pg.AxisItem = self.getAxis('bottom')
        bottom_axis.setHeight(45)
        bottom_axis.setStyle(tickFont=BOTTOM_AXIS_FONT)

        self.showGrid(x=True, y=False, alpha=0.8)

        self.text_label = None

    def init(self, time_list, freq: Freq):
        view: pg.ViewBox = self.getViewBox()
        self.init_axis(time_list, freq)
        view.sigXRangeChanged.connect(self._update_yrange)
        view.sigXRangeChanged.connect(self._update_vpvr)
        # self.proxy = pg.SignalProxy(view.sigXRangeChanged, rateLimit=60, slot=self._update_vpvr)
        xmax = len(self.getAxis('bottom')) - 1
        self.setLimits(xMax=xmax, maxXRange=xmax)

    def _update_yrange(self):
        view: pg.ViewBox = self.getViewBox()
        view_range = self.get_view_range()
        # [[12145.212864703284, 13592.760270060837], [2823.1710353818326, 3688.0489646181677]]
        x_start, x_end = math.floor(view_range[0][0]), math.ceil(view_range[0][1])
        try:
            base_line_item = self.items_dict['level0']  # todo: KeyError: 'level0'
        except KeyError as e:
            pass
        else:
            y_start, y_end = base_line_item.get_yrange(x_start, x_end)
            if y_start is not None:
                view.setYRange(y_start, y_end, padding=0.05)

    def _update_vpvr(self):
        vpvr_item_name_list = filter(lambda x: 'vpvr' in x, self.items_dict.keys())
        for vpvr_item_name in vpvr_item_name_list:
            view_range = self.get_view_range()
            if vpvr_item_name == 'vpvr':
                x_start = view_range[0][0]
                x_end = x_start + (view_range[0][1] - view_range[0][0]) * 0.382
            else:
                x_start = None
                x_end = None
            self.items_dict[vpvr_item_name].setXrange(view_range, x_start, x_end)

    def init_axis(self, time_list, freq: Freq):
        time_axis = self.getAxis('bottom')
        time_axis.init(time_list, freq)

    def remove_item(self, item_name):
        item = self.items_dict[item_name]
        self.removeItem(item)
        del self.items_dict[item_name]

    def clear_plot(self):
        item_name_list = list(self.items_dict.keys())
        for name in item_name_list:
            self.remove_item(name)
        self.clear()

    def add_line(self, x, y, penargs, name, *args, **kwargs):
        line_item = LineItem(name, *args, **kwargs)
        line_item.setData(x=x, y=y)
        line_item.setPen(pg.mkPen(penargs))
        line_item.setZValue(3)
        self.addItem(line_item)
        self.items_dict[name] = line_item

    def add_vpvr(self, price, volume, x_start, x_end, name='vpvr', **kwargs):
        self.configure_view_range()
        if name == 'vpvr':
            color = VPVR_COLOR
        else:
            color = UnitVPVR_COLOR
        vpvr_item = VPVRItem(color=color, **kwargs)
        view_range = self.get_view_range()
        if x_start is None:
            x_start = view_range[0][0]
            x_end = x_start + (view_range[0][1] - x_start) * 0.382
        vpvr_item.setData(price, volume, view_range, x_start, x_end)
        if name == 'vpvr':
            vpvr_item.setZValue(1)
        else:
            vpvr_item.setZValue(0)
        # vpvr_item.draw_text(self)
        self.addItem(vpvr_item, ignoreBounds=True)
        self.items_dict[name] = vpvr_item

    def add_price_label(self, price, name='price_label'):
        price_label_item = PriceLabelItem()
        price_label_item.setData(price=price)
        price_label_item.setZValue(4)
        self.addItem(price_label_item)
        self.items_dict[name] = price_label_item

    def get_view_range(self):
        return self.getViewBox().viewRange()

    def configure_view_range(self):
        view = self.getViewBox()
        data: LineItem = self.items_dict['level0']
        view_range = self.get_view_range()
        if (view_range[0][1] - view_range[0][0]) < 2:
            x_start = int(data.xData[-1] / 2)
            x_end = int(data.xData[-1] + 5 * self.getAxis('bottom').get_interval_base())
        else:
            x_start = view_range[0][0]
            x_end = view_range[0][1]
        y_start, y_end = data.get_yrange(x_start, x_end)
        view.setXRange(x_start, x_end, padding=0)
        if y_start is not None and y_end is not None:
            view.setYRange(y_start, y_end, padding=0.05)

    def configure_view_yrange(self):
        view = self.getViewBox()
        data: LineItem = self.items_dict['level0']
        view_range = self.get_view_range()
        x_start, x_end = view_range[0][0], view_range[0][1]
        y_start, y_end = data.get_yrange(x_start, x_end)
        view.setYRange(y_start, y_end, padding=0.05)

    def show_plot(self, show_data_list: list):
        for show_data in show_data_list:
            item_name = show_data['item_name']
            parameters = show_data['params']
            data = show_data['data']
            itemtype = show_data['itemtype']
            if itemtype is LineItem:
                self.add_line(name=item_name, **data, **parameters)
            elif itemtype is VPVRItem:
                self.add_vpvr(name=item_name, **data, **parameters)
            elif itemtype is PriceLabelItem:
                self.add_price_label(name=item_name, **data, **parameters)
            else:
                pass
        self.configure_view_range()

    def update_plot(self, update_data_list: list):
        if len(self.items_dict) == 0:
            return
        now_items_list = self.items_dict.keys()
        unitVPVR_item = list(filter(lambda x: 'vpvr_' in x, now_items_list))
        remove_flag = False
        for update_data in update_data_list:
            item_name = update_data['item_name']
            data = update_data['data']
            if item_name == 'level0':
                item = self.items_dict[item_name]
                item.update_data(**data)
                self.configure_view_yrange()
            elif item_name == 'vpvr':
                item = self.items_dict[item_name]
                view_range = self.get_view_range()
                x_start, x_end = view_range[0][0], view_range[0][0] + (view_range[0][1] - view_range[0][0]) * 0.382
                data['x_start'] = x_start
                data['x_end'] = x_end
                item.update_data(view_range=view_range, **data)
            elif 'vpvr_' in item_name:
                remove_flag = True
                if item_name in deepcopy(unitVPVR_item):
                    item = self.items_dict[item_name]
                    view_range = self.get_view_range()
                    item.update_data(view_range=view_range, **data)
                    unitVPVR_item.remove(item_name)
                else:
                    self.add_vpvr(name=item_name, **data)
            else:
                item = self.items_dict[item_name]
                item.update_data(**data)

        # 删除没有的vpvr_item
        if remove_flag and unitVPVR_item:
            for item_name in unitVPVR_item:
                self.remove_item(item_name)
