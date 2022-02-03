import datetime
import gc
import time

import numpy as np
import scipy.stats as stats
from scipy.signal import find_peaks
import pandas as pd

from VisionQuant.Analysis import Indicators
from VisionQuant.Analysis.StrategyBase import StrategyBase
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.Engine.AnalyzeEngine import AnalyzeEngine
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Code import Code
from VisionQuant.utils.Params import Market

nptype_point = np.dtype([('index', np.uint32), ('price', np.float64), ('max_level', np.uint8), ('gain', np.uint16)])
nptype_time_grav = np.dtype(
    [('start_point', nptype_point), ('end_point', nptype_point), ('volume', np.float64), ('flag', np.bool_)])
nptype_space_grav = np.dtype([('price', np.float64), ('volume', np.float64)])
nptype_zcyl = np.dtype([('price', np.float64), ('ratio', np.float64), ('last_point_index', np.uint32)])
# save_dir = 'D:/OneDrives/onedrive_102/OneDrive/策略log/Relavity/'
save_dir = 'E:/Onedrive/策略log/Relavity/'
# 引入pyc模块
from VisionQuant.Analysis.Relavity import relavity_cy
RELAVITY_MAX_LEVEL = 7


def get_peaks(zcyl_list):
    if len(zcyl_list) == 0 or np.max(zcyl_list['ratio']) < 1e-8:
        return []
    stand_ratio_list = zcyl_list['ratio'] / np.max(zcyl_list['ratio'])
    tmp_ratio_list = stand_ratio_list[np.where((stand_ratio_list > 0))]
    tmp_ratio_list = tmp_ratio_list[np.where(tmp_ratio_list <= np.percentile(tmp_ratio_list, 95))]
    min_limit = np.percentile(tmp_ratio_list, 25)
    # 在两端加0，以加入两端的峰值可能性
    zero_arr = np.array([0])
    stand_ratio_list = np.append(zero_arr, stand_ratio_list)
    stand_ratio_list = np.append(stand_ratio_list, zero_arr)
    idx, _ = find_peaks(stand_ratio_list, distance=1, height=min_limit)
    idx = idx - 1  # 去掉开头补0产生的位移
    tmp_list = zcyl_list[idx]
    return tmp_list


def equalize(data, bins=20):
    hist, bin_edges = np.histogram(data, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.
    cdf = hist.cumsum()
    # cdf = cdf / float(cdf[-1])
    out = np.interp(data, bin_centers, cdf)
    return out


class Relativity(StrategyBase):
    def __init__(self, code, local_data=None, show_result=False):
        super().__init__(code, local_data, show_result)
        self.kdata = None
        self.space_grav = None
        self.time_grav = None
        self.trend_dict = None
        self.zcyl = None
        self.indicators = []
        self.last_time = None
        self.last_price = None
        self.last_index = None
        self.max_level = RELAVITY_MAX_LEVEL
        self.min_step = 0.01

    def analyze(self):
        t = time.perf_counter()
        data = self.get_data()
        self.kdata = data.get_kdata('5')
        self.kdata.remove_zero_volume()  # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
        basic_finance_data = self.get_basic_finance_data()
        if basic_finance_data is None:
            all_capital = self.kdata.data['volume'].sum() / 9
        else:
            all_capital = basic_finance_data['流通股本']
        if len(self.kdata) <= 8640:
            print("数据太短啦")
            return None
        self.last_time = self.kdata.get_last_time()
        self.last_price = self.kdata.get_last_price()
        self.last_index = self.kdata.get_last_index()
        high = np.array(self.kdata.data['high'])
        low = np.array(self.kdata.data['low'])
        volume = np.array(self.kdata.data['volume'])
        if self.code.market in [Market.Ashare.MarketSH.ETF, Market.Ashare.MarketSZ.ETF]:
            self.min_step = 0.001
        else:
            self.min_step = 0.01
        t_read_data = time.perf_counter() - t

        t = time.perf_counter()
        self.time_grav = relavity_cy.TimeGravitation(high, low,
                                                     min_step=self.min_step,
                                                     max_level=int(RELAVITY_MAX_LEVEL))
        # print('calc particle', time.perf_counter() - t)
        #
        # t = time.perf_counter()
        time_grav_dict = self.time_grav.calc_time_grav_dict(volume)
        line_dist0 = time_grav_dict[0]
        # plt.hist(line_dist1['dindex'], 50)
        # plt.show()
        # plt.hist(np.log(line_dist1['dindex']+1),50)
        # plt.show()
        import scipy.stats as stats
        from copy import deepcopy
        # for line_dist in (line_dist1,line_dist2,line_dist3,line_dist4,line_dist5):
        #     data = line_dist['dindex']
        #     hist = np.bincount(data)
        #     x = np.arange(data.max()+1)
        #     cdf = np.cumsum(hist)
        #     cdf = cdf / cdf.max()
        #     idx = np.where(cdf>0.5)[0][0]
        #     print(x[idx])
        #     plt.plot(x, cdf)
        # plt.show()
        # line_dist3 = relavity_cy.calc_line_list(self.time_grav.get_points(2), volume)
        # line_dist2 = relavity_cy.calc_line_list(self.time_grav.get_points(1), volume)
        # line_dist1 = relavity_cy.calc_line_list(self.time_grav.get_points(0), volume)
        # print('calc line dist', time.perf_counter() - t)
        # t = time.perf_counter()
        self.space_grav = relavity_cy.SpaceGravitation(high, low, volume, all_capital, min_price_step=self.min_step)
        qhs_index = relavity_cy.calc_qhs_index(volume, all_capital)
        cm_dist0 = self.space_grav.get_grav_dist(self.last_index)
        cm_dist1 = self.space_grav.get_grav_dist(self.last_index, start_index=qhs_index[0])
        # cm_dist0, cm_dist1 = relavity_cy.calc_CM_combine(high, low, volume, all_capital, min_price_step=min_step)
        # print('calc cm dist', time.perf_counter() - t)
        # t = time.perf_counter()
        self.indicators = []
        mid_index = (-line_dist0['dindex'] + 2 * line_dist0['index']) / 2
        mid_price = line_dist0['price'] * (1 + 1 / (line_dist0['dprice'] + 1)) * 0.5
        ma_list = []
        self.trend_dict = dict()
        self.trend_dict['index'] = mid_index
        # ma_list_show = []
        for period in [3, 9, 27, 81, 243, 729]:
            tmp_ma = Indicators.EMA(mid_price, period)
            replace_val = tmp_ma[period - 1]
            np.nan_to_num(tmp_ma, copy=False, nan=replace_val)
            # ma_list_show.append({'name': 'junxian', 'index': mid_index, 'val': tmp_ma})
            ma_list.append(tmp_ma)
        ma = np.array(ma_list)
        all_lisandu = np.std(ma, axis=0) / np.mean(ma, axis=0)
        short_lisandu = np.std(ma[0:3], axis=0) / np.mean(ma[0:3], axis=0)
        long_lisandu = np.std(ma[2:5], axis=0) / np.mean(ma[2:5], axis=0)
        self.trend_dict['short'] = ma[0] * 0.309 + ma[1] * 0.309 + ma[2] * 0.191 + ma[3] * 0.191
        self.trend_dict['mid'] = ma[1] * 0.191 + ma[2] * 0.309 + ma[3] * 0.309 + ma[4] * 0.191
        self.trend_dict['long'] = ma[2] * 0.191 + ma[3] * 0.191 + ma[4] * 0.309 + ma[5] * 0.309

        def ma_filter(_data, _period):
            _data = Indicators.MA(_data, _period)
            _replace_val = _data[_period - 1]
            return np.nan_to_num(_data, nan=_replace_val)

        all_lisandu = ma_filter(all_lisandu, 8)
        short_lisandu = ma_filter(short_lisandu, 8)
        long_lisandu = ma_filter(long_lisandu, 8)
        # print(np.mean(line_dist1['dindex']))
        # i = 12  # 平均一天12笔
        # buy_dindex_sum = 0
        # sell_dindex_sum = 0
        # buy_dvol_sum = 0.0
        # sell_dvol_sum = 0.0
        # vol_index = []
        # buy_index = []
        # sell_index = []
        # final_index = []
        # final_index_new = []
        # test_index = []
        # while i < line_dist1.shape[0]:
        #     tmp_line_dist = line_dist1[i - 12:i]
        #     for item in tmp_line_dist:
        #         if item['dprice'] > 0:
        #             buy_dindex_sum += item['dindex']
        #             buy_dvol_sum += item['buyvol']
        #         else:
        #             sell_dindex_sum += item['dindex']
        #             sell_dvol_sum += item['sellvol']
        #     vol_index.append(round((line_dist1[i]['index']+line_dist1[i-24]['index']) / 2))
        #     buy_index.append(buy_dvol_sum / buy_dindex_sum)
        #     sell_index.append(sell_dvol_sum / sell_dindex_sum)
        #     test_index.append((buy_dvol_sum+sell_dvol_sum) / (buy_dindex_sum+sell_dindex_sum))
        #     final_index.append(1 / (1 + sell_dvol_sum / buy_dvol_sum))
        #     final_index_new.append(1 / (1 + (sell_dvol_sum / sell_dindex_sum) / (buy_dvol_sum / buy_dindex_sum)))
        #     buy_dvol_sum = 0.0
        #     sell_dvol_sum = 0.0
        #     buy_dindex_sum = 0
        #     sell_dindex_sum = 0
        #     i += 1
        # final_index = Indicators.EMA(np.array(final_index), 6)
        # final_index_new = Indicators.EMA(np.array(final_index_new), 6)
        # self.indicators.append(
        #     {'name': 'mfi', 'index': vol_index, 'val': [buy_index, sell_index, final_index, final_index_new,test_index]})

        for level, line_dist in time_grav_dict.items():
            index = line_dist['index']
            width = line_dist['dindex']
            dl = line_dist['dindex']
            # dp = line_dist['dprice']
            # buy_mask = np.where(dp > 0, 1, 0)
            # sell_mask = np.where(dp < 0, 1, 0)
            # dp = (dp - np.min(dp)) / (np.max(dp) - np.min(dp))
            # v = line_dist['volume']
            # val = v * (np.log2(1 + dp) + 0.0001) / dl
            # minus_list = np.where(line_dist['dprice'] < 0)
            # val[minus_list] *= -1
            mean_allvol = (line_dist['buyvol'] + line_dist['sellvol']) / (
                    line_dist['sellindex'] + line_dist['buyindex'])
            line_dist['buyindex'][np.where(line_dist['buyindex'] == 0)] = 1
            line_dist['sellindex'][np.where(line_dist['sellindex'] == 0)] = 1
            mean_buyvol = line_dist['buyvol'] / line_dist['buyindex']
            mean_sellvol = line_dist['sellvol'] / line_dist['sellindex']
            # buyvol = all_vol * buy_mask / dl
            # sellvol = all_vol * sell_mask / dl
            self.indicators.append(
                {'name': '平均成交量 级别{}'.format(level),
                 'val': {'index': index, 'width': width, 'buyvol': mean_buyvol, 'sellvol': mean_sellvol,
                         'allvol': mean_allvol}})
        self.indicators.append({'name': '均线离散度',
                                'val': {'index': mid_index, 'short': short_lisandu, 'long': long_lisandu,
                                        'all': all_lisandu}})
        short_mtm, mid_mtm, long_mtm = Indicators.MTM(self.trend_dict['short'], self.trend_dict['mid'],
                                                      self.trend_dict['long'])
        short_trend, long_trend = Indicators.trend(self.trend_dict['short'], self.trend_dict['mid'],
                                                   self.trend_dict['long'])
        self.indicators.append({'name': 'MTM',
                                'val': {'index': mid_index, 'short': short_mtm, 'mid': mid_mtm, 'long': long_mtm}})
        self.indicators.append({'name': 'Trend',
                                'val': {'index': mid_index, 'short': short_trend, 'long': long_trend}})
        # print('calc indicators list', time.perf_counter() - t)
        #
        # t = time.perf_counter()
        tmp = self.time_grav.get_ratio()
        tmp['ratio'] = tmp['ratio'] / np.sqrt(1 + np.power((tmp['price'] / self.last_price - 1) / 0.1, 8))
        tmp['ratio'] = tmp['ratio'] / np.max(tmp['ratio'])
        tmp_lp_set, tmp_hp_set = self.filter_peak_list(tmp, self.last_price)
        if len(tmp_lp_set) >= 5:
            tmp_lp_set1 = get_peaks(tmp_lp_set)
            if len(tmp_lp_set1) >= 3:
                tmp_lp_set = tmp_lp_set1
            else:
                tmp_lp_set = np.sort(tmp_lp_set, order='ratio', kind='stable')[-3:]
        elif len(tmp_lp_set) > 0:
            tmp_lp_set = tmp_lp_set[np.argmax(tmp_lp_set['ratio'])]
        else:
            tmp_lp_set = []
        if len(tmp_hp_set) >= 5:
            tmp_hp_set1 = get_peaks(tmp_hp_set)
            if len(tmp_hp_set1) >= 2:
                tmp_hp_set = tmp_hp_set1
            else:
                tmp_hp_set = np.sort(tmp_hp_set, order='ratio', kind='stable')[-3:]
        elif len(tmp_hp_set) > 0:
            tmp_hp_set = tmp_hp_set[np.argmax(tmp_hp_set['ratio'])]
        else:
            tmp_hp_set = []
        if len(tmp_hp_set) > 4:
            tmp_hp_set = np.sort(tmp_hp_set, order='ratio', kind='stable')[-4:]
        if len(tmp_lp_set) > 4:
            tmp_lp_set = np.sort(tmp_lp_set, order='ratio', kind='stable')[-4:]

        if len(tmp_hp_set) > 0 and len(tmp_lp_set) > 0:
            zcyl_set = np.append(tmp_hp_set, tmp_lp_set)
        elif len(tmp_hp_set) > 0 and len(tmp_lp_set) == 0:
            zcyl_set = tmp_hp_set
        elif len(tmp_hp_set) == 0 and len(tmp_lp_set) > 0:
            zcyl_set = tmp_lp_set
        else:
            raise RuntimeError("无支撑压力")
        self.zcyl = zcyl_set
        # print('calc peak dist', time.perf_counter() - t)
        t_analyze = time.perf_counter() - t
        print("分析{}完成, 读取数据用时:{:.4f}s 分析用时:{:.4f}s".format(self.code.code, t_read_data, t_analyze))
        if self.show_result:
            obj = RelavitiyVisualize(figure_title=self.code.code + ' ' + TimeTool.time_to_str(self.last_time),
                                     indicators_num=len(self.indicators),
                                     min_step=self.min_step)
            obj.draw_main(points_set=self.time_grav.get_all_points(), last_price=self.last_price)
            obj.draw_zcyl(zcyl_list=zcyl_set)
            obj.draw_CM(space_gravitation_dist=cm_dist0)
            obj.draw_CM_sum(space_gravitation_dist=cm_dist1)
            obj.draw_qhs(qhs_index_list=qhs_index)
            obj.draw_indicators(indicators_list=self.indicators)
            # obj.draw_junxian(ma_list=ma_list_show)
            # obj.draw_minp_line(min_price_list)
            # obj.draw_ori_zcyl(zcyl_list=tmp_p_set)
            obj.save(self.code.code + '_' + TimeTool.time_to_str(self.last_time, fmt='%Y%m%d%H%M%S'))
            # obj.show()

    def analyze_score(self):
        # t = time.perf_counter()
        data = self.get_data()
        self.kdata = data.get_kdata('5')
        self.kdata.remove_zero_volume()  # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
        if len(self.kdata) <= 8640:
            print("{}数据太短啦, 开始时间{}, 结束时间{}".format(self.code.code,
                                                   TimeTool.time_to_str(self.kdata.get_start_time()),
                                                   TimeTool.time_to_str(self.kdata.get_last_time())))
            return None
        # t_read_data = time.perf_counter() - t
        # t = time.perf_counter()
        high = np.array(self.kdata.data['high'])
        low = np.array(self.kdata.data['low'])
        if self.code.market in [Market.Ashare.MarketSH.ETF, Market.Ashare.MarketSZ.ETF]:
            self.min_step = 0.001
        else:
            self.min_step = 0.01

        self.time_grav = relavity_cy.TimeGravitation(high, low, min_step=self.min_step, max_level=RELAVITY_MAX_LEVEL)
        score = self.time_grav.get_score()
        # t_analyze = time.perf_counter() - t
        # print("分析{}完成, 日期:{}, 得分:{}, 读取数据用时:{:.4f}s 分析用时:{:.4f}s".format(
        #     self.code.code, TimeTool.time_to_str(self.kdata.get_last_time(), '%Y-%m-%d'), score, t_read_data,
        #     t_analyze))
        return score

    @staticmethod
    def filter_peak_list(peak_list, filter_price):
        low_p_set = peak_list[np.where(peak_list['price'] <= filter_price)]
        high_p_set = peak_list[np.where(peak_list['price'] >= filter_price)]
        return low_p_set, high_p_set

    @staticmethod
    def recalc_ratio(tmp_peak_set, p, peak_count):
        def func(price_list, _a, _p, _phi):
            return np.exp(np.log(_phi) / np.power(_a - 1, 4) * np.power(price_list / _p - 1, 4))

        mean_peak_price = np.mean(tmp_peak_set['price'])
        a = mean_peak_price / p
        phi = np.exp(-np.power(len(tmp_peak_set) / max(5, (peak_count / 4)), np.pi))
        tmp_peak_set['ratio'] *= func(tmp_peak_set['price'], a, p, phi)
        return tmp_peak_set

    def show(self, points_set, zcyl_list, cm_dist):
        obj = RelavitiyVisualize(figure_title=self.code.code + ' ' + TimeTool.time_to_str(self.last_time),
                                 indicators_num=1)
        obj.draw_main(points_set, self.last_price)
        obj.draw_zcyl(zcyl_list)
        obj.draw_CM(cm_dist)
        obj.show()


class RelavitiyVisualize(object):
    def __init__(self, figure_title=None, indicators_num=1, min_step=0.01):
        plt.figure(figsize=(12 + indicators_num * 3, 8 + indicators_num * 2))
        self.grid = plt.GridSpec(38 + indicators_num * 5, 36)
        self.cm_ax = plt.subplot(self.grid[0:36, 30:36])
        self.main_ax = plt.subplot(self.grid[0:36, 0:30], sharey=self.cm_ax)
        if figure_title is not None:
            plt.title(figure_title)
        self.indicators_ax = [plt.subplot(self.grid[38 + i * 5:38 + (i + 1) * 5, 0:30], sharex=self.main_ax)
                              for i in range(indicators_num)]
        self.x_max_limit = 20000
        self.x_min = 0
        self.y_min = 0
        self.y_max = 0
        self.min_step = min_step
        self.last_price = None
        self.last_index = None

    def draw_main(self, points_set, last_price):
        self.last_price = last_price
        ax = self.main_ax
        tmp = points_set[0]
        self.last_index = tmp['index'][-1]
        self.x_min = self.last_index - 90 * 48 - 50
        for level, points_list in points_set.items():
            index_list = points_list['index']
            price_list = points_list['price']
            if level == 0:
                ax.plot(index_list, price_list, label=level, linewidth=0.7 + level * 0.05,
                        alpha=0.7 + level * 0.05)
            else:
                ax.plot(index_list[:-1], price_list[:-1], label=level, linewidth=0.7 + level * 0.05,
                        alpha=0.7 + level * 0.05)
        ax.axhline(y=self.last_price, color='black', linestyle='--', alpha=0.6)
        offset = self.last_price / 1000
        if self.min_step == 0.01:
            ax.text(self.last_index + 110, last_price + offset, '{:.2f}'.format(last_price),
                    c='black', fontsize=7)
        else:
            ax.text(self.last_index + 110, last_price + offset, '{:.3f}'.format(last_price),
                    c='black', fontsize=7)

        tmp = tmp[np.where(tmp['index'] > self.x_min)]
        self.y_max = max(tmp['price'].max(), self.last_price) * 1.005
        self.y_min = min(tmp['price'].min(), self.last_price) * 0.992
        ax.set_xlim(self.x_min, self.last_index + 250)
        ax.set_ylim(self.y_min, self.y_max)
        locator_major_x = MultipleLocator(240)
        locator_minor_x = MultipleLocator(48)
        locator_major_y = MultipleLocator(round((self.y_max - self.y_min) / 10, round(np.log10(1.0 / self.min_step))))
        locator_minor_y = MultipleLocator(round((self.y_max - self.y_min) / 100, round(np.log10(1.0 / self.min_step))))
        ax.xaxis.set_major_locator(locator_major_x)
        ax.xaxis.set_minor_locator(locator_minor_x)
        ax.yaxis.set_major_locator(locator_major_y)
        ax.yaxis.set_minor_locator(locator_minor_y)
        ax.xaxis.grid(which='major', alpha=0.5, linewidth=0.5)
        ax.xaxis.grid(which="minor", linestyle=':', alpha=0.4, linewidth=0.5)

    def draw_junxian(self, ma_list):
        ax = self.main_ax
        for ma in ma_list:
            index = ma['index']
            val = ma['val']
            ax.plot(index, val)

    def draw_CM(self, space_gravitation_dist):
        ax = self.cm_ax
        bar_height = (space_gravitation_dist['price'][1] - space_gravitation_dist['price'][0]) * 0.7
        std_volume_list = space_gravitation_dist['volume'] / np.max(space_gravitation_dist['volume'])
        ax.barh(y=space_gravitation_dist['price'], width=std_volume_list, height=bar_height,
                alpha=0.6, color='purple')
        cdf = np.cumsum(std_volume_list / np.sum(std_volume_list))
        ax.plot(cdf, space_gravitation_dist['price'], alpha=0.6, color='gold')
        locator_major = FixedLocator([0.2, 0.4, 0.5, 0.6, 0.8, 1])
        locator_minor = MultipleLocator(0.05)
        ax.xaxis.set_major_locator(locator_major)
        ax.xaxis.set_minor_locator(locator_minor)
        ax.xaxis.grid(which='major', linestyle=':', alpha=0.7, linewidth=0.5)

    def draw_CM_sum(self, space_gravitation_dist):
        ax = self.cm_ax
        bar_height = (space_gravitation_dist['price'][1] - space_gravitation_dist['price'][0]) * 0.7
        std_volume_list = space_gravitation_dist['volume'] / np.max(space_gravitation_dist['volume'])
        ax.barh(y=space_gravitation_dist['price'],
                width=std_volume_list,
                height=bar_height,
                alpha=0.4, color='green')
        cdf = np.cumsum(std_volume_list / np.sum(std_volume_list))
        ax.plot(cdf, space_gravitation_dist['price'], alpha=0.8, color='skyblue')

    def draw_zcyl(self, zcyl_list):
        ax = self.main_ax
        offset = self.last_price / 1000
        for peak in zcyl_list:
            if peak['price'] >= self.last_price:
                ax.axhline(y=peak['price'], color='darkgreen', linestyle='--', alpha=0.6)
                ax.text(self.last_index + 10, peak['price'] + offset, '{:.3f}'.format(peak['ratio']),
                        c='darkgreen', fontsize=7)
                if self.min_step == 0.01:
                    ax.text(self.last_index + 110, peak['price'] + offset, '{:.2f}'.format(peak['price']),
                            c='darkgreen', fontsize=7)
                else:
                    ax.text(self.last_index + 110, peak['price'] + offset, '{:.3f}'.format(peak['price']),
                            c='darkgreen', fontsize=7)
                if peak['price'] > self.y_max / 1.005:
                    self.y_max = peak['price'] * 1.005
            else:
                ax.axhline(y=peak['price'], color='darkred', linestyle='--', alpha=0.6)
                ax.text(self.last_index + 10, peak['price'] - offset, '{:.3f}'.format(peak['ratio']),
                        c='darkred', fontsize=7, verticalalignment='top')
                if self.min_step == 0.01:
                    ax.text(self.last_index + 110, peak['price'] - offset, '{:.2f}'.format(peak['price']),
                            c='darkred', fontsize=7, verticalalignment='top')
                else:
                    ax.text(self.last_index + 110, peak['price'] - offset, '{:.3f}'.format(peak['price']),
                            c='darkred', fontsize=7, verticalalignment='top')
                if peak['price'] < self.y_min / 0.992:
                    self.y_min = peak['price'] * 0.992
        ax.set_ylim(self.y_min, self.y_max)

    def draw_qhs(self, qhs_index_list):
        ax = self.main_ax
        for index in qhs_index_list:
            ax.axvline(x=index, ls=":", c="orange")

    def draw_indicators(self, indicators_list):
        ax_list = self.indicators_ax

        def normalization(_val):
            _val = np.abs(_val)
            _range = np.max(_val) - np.min(_val)
            _val = (_val - np.min(_val)) / _range
            _val = np.power(_val, 0.5)
            return _val

        for ax, indicator in zip(ax_list, indicators_list):
            if indicator['name'] == 'lisandu':
                for line in indicator['val']:
                    ax.plot(indicator['index'], line)
                show_idx = np.where(indicator['index'] > self.x_min)
                max_val = np.max(indicator['val'][1][show_idx])
                ax.set_ylim(0, max_val * 1.1)
                ax.xaxis.grid(which='major', alpha=0.5, linewidth=0.5)
                ax.xaxis.grid(which="minor", linestyle=':', alpha=0.4, linewidth=0.5)
            elif indicator['name'] == 'mvol':
                index = indicator['index']
                val = indicator['val']
                show_idx = np.where(index > self.x_min)
                color = ['red' if v > 0 else 'green' for v in val]
                val = normalization(val)
                show_val = np.array(val)[show_idx]
                ax.scatter(index, val, color=color)
                ax.set_ylim(show_val.min() * 0.5, show_val.max() * 1.1)
                ax.xaxis.grid(which='major', alpha=0.5, linewidth=0.5)
                ax.xaxis.grid(which="minor", linestyle=':', alpha=0.4, linewidth=0.5)
            elif indicator['name'] == 'vol':
                val = indicator['val']
                index = val['index']
                width = val['width']
                index = index - width
                buyvol, sellvol = val['buyvol'], val['sellvol']
                # buyvol = np.log2(1+buyvol)
                # sellvol = np.log2(1+sellvol)
                show_idx = np.where(index > self.x_min)
                all_vol = buyvol + sellvol
                all_vol = np.log2(1 + all_vol)
                show_vol = np.array(all_vol)[show_idx]
                buyvol = np.log2(1 + buyvol)
                sellvol = np.log2(1 + sellvol)
                buy_index = np.where(buyvol > 0)[0]
                sell_index = np.where(sellvol > 0)[0]
                buy_x = (index + width / 2)[buy_index]
                sell_x = (index + width / 2)[sell_index]
                # show_vol_equalize = equalize(show_vol, 100)
                # coeff = show_vol_equalize / show_vol
                # buyvol[show_idx] *= coeff
                # sellvol[show_idx] *= coeff
                # ax.bar(index, buyvol, width=width, align='edge', color='red')
                # ax.bar(index, sellvol, width=width, align='edge', color='green', alpha=.5)
                # ax.plot(index + width / 2, all_vol, alpha=.5)
                sellvol_show = sellvol[sell_index]
                buyvol_show = buyvol[buy_index]
                ax.scatter(sell_x, sellvol_show, color='green', s=12)
                ax.scatter(buy_x, buyvol_show, color='red', s=12)

                ax.set_ylim(show_vol.min() * 0.99, show_vol.max() * 1.005)
                ax.xaxis.grid(which='major', alpha=0.5, linewidth=0.5)
                ax.xaxis.grid(which="minor", linestyle=':', alpha=0.4, linewidth=0.5)
            elif indicator['name'] == 'mfi':
                val = indicator['val']
                index = indicator['index']
                # ax.plot(index, val[2])
                # ax.plot(index, val[3])
                # ax.axhline(0.5)
                # ax.plot(index, val[0])
                # ax.plot(index, val[1])
                ax.plot(index, val[4])

    def draw_minp_line(self, minp_list):
        ax = self.cm_ax
        for minp in minp_list:
            ax.axhline(minp, color='blue', linestyle='-')

    def draw_ori_zcyl(self, zcyl_list):
        ax = self.cm_ax
        bar_height = (zcyl_list['price'][1] - zcyl_list['price'][0]) * 0.7
        # plt.plot(space_gravitation_dist.volume_list, space_gravitation_dist.price_list)
        ax.barh(y=zcyl_list['price'], width=zcyl_list['ratio'], height=bar_height,
                alpha=0.6)

    @staticmethod
    def show():
        plt.show()

    @staticmethod
    def save(fname):
        plt.savefig(save_dir + fname, dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import gc, time
    from matplotlib.ticker import MultipleLocator, FixedLocator

    end_time = TimeTool.str_to_dt('2021-08-01 15:00:00')
    start_time = end_time - datetime.timedelta(days=365+180)
    start_time = start_time.replace(hour=9, minute=0, second=0)
    test_code_list = ['002273', '002382', '601456', '002492', '001979', '002584', '999999', '399006', '399001']
    test_code_list1 = ['600519']
    for test_code in test_code_list1:
        t_code = Code(test_code, '5', start_time, end_time=end_time,
                      data_source={'local': DataSource.Local.VQapi, 'live': DataSource.Live.VQapi})
        test_strategy = Relativity(code=t_code, show_result=True)
        test_score = test_strategy.analyze_score()
        print('{} {}'.format(test_code, test_score))
        # time.sleep(8)
        # plt.clf()
        gc.collect()
