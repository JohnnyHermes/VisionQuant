import time

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph import InfiniteLine, ScatterPlotItem, PlotDataItem

from VQGUI.VQChart.ChartItem import LineItem, VPVRItem, PriceLabelItem
from VQGUI.VQChart.Params import WHITE_COLOR
from VisionQuant.Analysis.Relativity.Relativity import Relativity

color_list = ['#b3b3b3', '#8da0cb', '#fc8d62', '#66c2a5', '#e78ac3', '#a6d854', '#ffd92f', '6666cc']
indi_color_list = ['#b3b3b3', '#8da0cb', '#fc8d62', '#66c2a5', '#e78ac3', '#a6d854', '#ffd92f']


def line_data_protocol(ana_result: Relativity):
    itemtype = LineItem
    points_dict = ana_result.time_grav.get_all_points()
    res = []
    for level, points in points_dict.items():
        item_name = 'level{}'.format(level)
        params = dict()
        data = dict()
        if level == 0:
            x, y = points['index'], points['price']
        else:
            # x, y = points['index'], points['price']
            x, y = points['index'][:-1], points['price'][:-1]
        data['x'] = x
        data['y'] = y
        if level <= 3:
            penargs = {'color': color_list[level], 'width': 1}
        else:
            penargs = {'color': color_list[level], 'width': 2}
        params['penargs'] = penargs

        res.append({'item_name': item_name,
                    'params': params,
                    'data': data,
                    'itemtype': itemtype})
    return res


def indicator_protocol(ana_result, ind_name, **kwargs):
    data = ana_result.calc_indicator(ind_name, **kwargs)
    if ind_name == '累积成交量':
        return _ind_volsum_protocol(data, **kwargs)
    if ind_name == '买卖成交量':
        return _ind_bsvol_protocol(data, **kwargs)
    if ind_name == 'VMACD':
        return _ind_VMACD_protocol(data, **kwargs)
    if ind_name == 'DP':
        return _ind_DP_protocol(data, **kwargs)
    if ind_name == 'BSDP':
        return _ind_BSDP_protocol(data, **kwargs)
    if ind_name == 'DPMACD':
        return _ind_DPMACD_protocol(data, **kwargs)
    if ind_name == 'UnitVol':
        return _ind_unitvol_protocol(data, **kwargs)


def _ind_unitvol_protocol(data, **kwargs):
    itemtype = LineItem
    item_name = 'indicator_unitvol'
    res = []
    params = dict()
    penargs = {'color': '#66ccff', 'width': 1}
    params['penargs'] = penargs
    _data = {'x': data['x'], 'y': data['volume']}
    res.append({'item_name': item_name,
                'params': params,
                'data': _data,
                'itemtype': itemtype})
    return res


def _ind_BSDP_protocol(data: dict, **kwargs):
    itemtype = LineItem
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    for y_name in y_names:
        item_name = 'indicator_BSDP_{}'.format(y_name)
        params = dict()
        if y_name == 'risedp':
            penargs = {'color': '#cc0000', 'width': 1}
        else:
            penargs = {'color': '#00cc00', 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})
    return res


def _ind_DPMACD_protocol(data: dict, **kwargs):
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    for y_name in y_names:
        item_name = 'indicator_DPMACD_{}'.format(y_name)
        params = dict()
        if y_name == 'dif':
            itemtype = LineItem
            penargs = {'color': '#ffffff', 'width': 1}
        elif y_name == 'dea':
            itemtype = LineItem
            penargs = {'color': '#ffff00', 'width': 1}
        else:
            itemtype = LineItem
            penargs = {'color': '#ffccff', 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})

    # hline
    itemtype = InfiniteLine
    params = {'pos': 0, 'angle': 0, 'pen': pg.mkPen(WHITE_COLOR)}
    _data = {}
    item_name = 'indicator_DPMACD_hline'
    res.append({'item_name': item_name,
                'params': params,
                'data': _data,
                'itemtype': itemtype})
    return res


def _ind_DP_protocol(data: dict, **kwargs):
    itemtype = LineItem
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    i = 0
    for y_name in y_names:
        item_name = 'indicator_DP_{}'.format(y_name)
        params = dict()
        penargs = {'color': color_list[i], 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})
        i += 1
    ma_list = kwargs.get('ma', None)
    if ma_list:
        for ma in ma_list:
            item_name = 'indicator_DP_ma{}'.format(ma)
            params = dict()
            penargs = {'color': color_list[i], 'width': 1}
            params['penargs'] = penargs
            mean_vol = np.array(pd.Series(data['dp']).rolling(window=int(ma), min_periods=int(ma)).mean())
            fill_val = mean_vol[ma]
            np.nan_to_num(mean_vol, copy=False, nan=fill_val)
            _data = {'x': data['x'], 'y': mean_vol}
            res.append({'item_name': item_name,
                        'params': params,
                        'data': _data,
                        'itemtype': itemtype})
    return res


def _ind_volsum_protocol(data: dict, **kwargs):
    itemtype = LineItem
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    i = 0
    for y_name in y_names:
        item_name = 'indicator_volsum_{}'.format(y_name)
        params = dict()
        penargs = {'color': color_list[i], 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})
        i += 1
    ma_list = kwargs.get('ma', None)
    if ma_list:
        for ma in ma_list:
            item_name = 'indicator_volsum_ma{}'.format(ma)
            params = dict()
            penargs = {'color': color_list[i], 'width': 1}
            params['penargs'] = penargs
            mean_vol = np.array(pd.Series(data['vol']).rolling(window=int(ma), min_periods=int(ma)).mean())
            fill_val = mean_vol[ma]
            np.nan_to_num(mean_vol, copy=False, nan=fill_val)
            _data = {'x': data['x'], 'y': mean_vol}
            res.append({'item_name': item_name,
                        'params': params,
                        'data': _data,
                        'itemtype': itemtype})
    return res


def _ind_bsvol_protocol(data: dict, **kwargs):
    itemtype = LineItem
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    for y_name in y_names:
        item_name = 'indicator_bsvol_{}'.format(y_name)
        params = dict()
        if y_name == 'buyvol':
            penargs = {'color': '#cc0000', 'width': 1}
        else:
            penargs = {'color': '#00cc00', 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})
    return res


def _ind_VMACD_protocol(data: dict, **kwargs):
    res = []
    y_names = list(data.keys())
    y_names.remove('x')
    for y_name in y_names:
        item_name = 'indicator_VMACD_{}'.format(y_name)
        params = dict()
        if y_name == 'dif':
            itemtype = LineItem
            penargs = {'color': '#ffffff', 'width': 1}
        elif y_name == 'dea':
            itemtype = LineItem
            penargs = {'color': '#ffff00', 'width': 1}
        else:
            itemtype = LineItem
            penargs = {'color': '#ffccff', 'width': 1}
        params['penargs'] = penargs
        _data = {'x': data['x'], 'y': data[y_name]}
        res.append({'item_name': item_name,
                    'params': params,
                    'data': _data,
                    'itemtype': itemtype})

    # hline
    itemtype = InfiniteLine
    params = {'pos': 0, 'angle': 0, 'pen': pg.mkPen(WHITE_COLOR)}
    _data = {}
    item_name = 'indicator_VMACD_hline'
    res.append({'item_name': item_name,
                'params': params,
                'data': _data,
                'itemtype': itemtype})
    return res


def now_price_protocol(ana_result):
    itemtype = PriceLabelItem
    item_name = 'now_price_label'
    params = dict()
    data = dict()
    data['price'] = ana_result.last_price
    res = [{'item_name': item_name,
            'params': params,
            'data': data,
            'itemtype': itemtype}]
    return res


def vpvr_data_protocol(ana_result, x_range_list: list, name_list: list):
    res = []
    for x_range, name in zip(x_range_list, name_list):
        x_start, x_end = x_range
        _x_start = x_start if x_start is not None else 0
        _x_end = x_end if x_end is not None else ana_result.last_index
        space_grav = ana_result.space_grav.get_grav_dist(end_index=_x_end, start_index=_x_start)
        itemtype = VPVRItem
        item_name = name
        params = dict()
        if x_start is not None:
            min_price = np.min(ana_result.kdata.data['low'][_x_start:_x_end])
            max_price = np.max(ana_result.kdata.data['high'][_x_start:_x_end])
            idx = np.where((min_price - ana_result.min_step / 2 < space_grav['price']) &
                           (max_price + ana_result.min_step / 2 > space_grav['price']))
            res.append({
                'item_name': item_name,
                'params': params,
                'data': {'price': space_grav['price'][idx],
                         'volume': space_grav['volume'][idx],
                         'x_start': x_start, 'x_end': x_end},
                'itemtype': itemtype
            })
        else:
            res.append({
                'item_name': item_name,
                'params': params,
                'data': {'price': space_grav['price'],
                         'volume': space_grav['volume'],
                         'x_start': x_start, 'x_end': x_end},
                'itemtype': itemtype
            })
    return res
