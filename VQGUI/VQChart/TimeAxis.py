import math
from typing import List

import pyqtgraph as pg
from PySide6 import QtGui
from pyqtgraph import debug

from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import Freq, MarketType

from VQGUI.VQChart.Params import AXIS_WIDTH, NORMAL_FONT, CURSOR_COLOR, BLACK_COLOR
import numpy as np


class TimeAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(orientation='bottom', *args, **kwargs)

        self.setPen(width=AXIS_WIDTH)
        self.tickFont: QtGui.QFont = NORMAL_FONT
        self._time_list = None
        self._string_fmt = None
        self._interval_base = 0
        self._future_time_list = None
        self.enableAutoSIPrefix(False)

    def init(self, time_list, freq: Freq):
        if freq == Freq.MIN1:
            self._interval_base = 240
        elif freq == Freq.MIN5:
            self._interval_base = 48
        elif freq == Freq.MIN15:
            self._interval_base = 16
        elif freq == Freq.MIN30:
            self._interval_base = 8
        elif freq == Freq.DAY:
            self._interval_base = 5
        else:
            self._interval_base = 8
        if freq in [Freq.MIN1, Freq.MIN5, Freq.MIN15, Freq.MIN30, Freq.MIN60, Freq.MIN120, Freq.MIN240]:
            self._string_fmt = '%Y-%m-%d\n%H:%M'
        else:
            self._string_fmt = '%Y-%m-%d'
        self.set_time_list(time_list)

    def tickSpacing(self, minVal, maxVal, size):
        # First check for override tick spacing

        dif = abs(maxVal - minVal)
        if dif == 0:
            return []

        intervals = np.array([0.125, 0.25, 0.5, 1, 5, 10, 20, 60, 120, 250]) * self._interval_base

        best_spacing = dif / 8
        minorIndex = 0
        while intervals[minorIndex + 1] <= best_spacing:
            minorIndex += 1

        levels = [
            (intervals[minorIndex + 1], 0),
            (intervals[minorIndex], 0),
            # (intervals[minorIndex], 0)    ## Pretty, but eats up CPU
        ]

        return levels

    def tickValues(self, minVal, maxVal, size):
        if self._time_list is None:
            return []
        ticks = []
        tickLevels = self.tickSpacing(minVal, maxVal, size)
        allValues = np.array([])
        for i in range(len(tickLevels)):
            spacing, offset = tickLevels[i]

            # determine starting tick
            start = (math.ceil((minVal - offset) / spacing) * spacing) + offset

            # determine number of ticks
            num = int((maxVal - start) / spacing) + 1
            values = (np.arange(num) * spacing + start)
            # remove any ticks that were present in higher levels
            # we assume here that if the difference between a tick value and a previously seen tick value
            # is less than spacing/100, then they are 'equal' and we can ignore the new tick.
            values = list(filter(lambda x: np.all(np.abs(allValues - x) > spacing * 0.01), values))
            allValues = np.concatenate([allValues, values])
            ticks.append((spacing / self.scale, values))

        return ticks

    def tickStrings(self, values, scale: float, spacing: int) -> list:
        """
        Convert original index to datetime string.
        """
        # Show no axis string if spacing smaller than 1
        if spacing < 1 or self._time_list is None:
            return ["" for i in values]
        values = np.array(list(filter(lambda x: len(self._time_list) > x >= 0, values)), dtype=int)
        strings = [t for t in self._time_list[values]]
        # print(strings)
        return strings

    def get_tickstring(self, value: int):
        return self._time_list[value]

    def set_time_list(self, time_list):
        if not isinstance(time_list, np.ndarray):
            time_list = np.array(time_list)

        self._time_list = [TimeTool.time_to_str(t, self._string_fmt) for t in time_list]
        self._future_time_list = TimeTool.generate_future_time_list(MarketType.Ashare.SH.STOCK, Freq.MIN1,
                                                                    time_list[-1])
        i = len(self._time_list) - 1
        first_future_timestr = self._future_time_list[0]
        while i > 0:
            if self._time_list[i] <= first_future_timestr:
                break
            i -= 1
        self._time_list = self._time_list[:i] + self._future_time_list
        self._time_list = np.array(self._time_list)

    def __len__(self):
        return len(self._time_list)

    def get_interval_base(self):
        return self._interval_base


