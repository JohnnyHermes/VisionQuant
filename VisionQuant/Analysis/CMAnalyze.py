import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from VisionQuant.Analysis import Indicators


def single_K_CM(volumelist, n, add_volume, min_idx):
    volumelist[min_idx:min_idx + n] = add_volume
    return volumelist


def calc_CM(kdata):
    # 先得到最大最小值
    high = round(kdata.high.max(), 2)
    low = round(kdata.low.min(), 2)
    step = round((high - low) / 400, 2)
    if step < 0.01:
        step = round(0.01, 2)
    pricelist = []
    tmp_price = low
    while 1:
        pricelist.append(round(tmp_price, 2))
        if not tmp_price <= high:
            break
        else:
            tmp_price = round(tmp_price + step, 2)
    # 最后加astype转换成Int类型才可以做数组的index
    n_list = np.round((kdata['high'].values - kdata['low'].values) / step + 1).astype(int)  # 单根k线跨越了几个价位
    min_idx_list = np.round((kdata['low'].values - pricelist[0]) / step).astype(int)  # 最小价位在pricelist中的index
    add_volume_list = np.round(kdata['volume'].values / n_list).astype(int)  # 每个价位要加的成交量 均匀分布
    volumelist = np.zeros((len(kdata), len(pricelist)))
    for i, n, add_volume, min_idx in zip(range(len(kdata)), n_list, add_volume_list, min_idx_list):
        for j in range(n):
            volumelist[i][min_idx + j] = add_volume
    df = pd.DataFrame(data=volumelist, columns=pricelist, index=kdata.time.values)
    return df


class CM:
    def __init__(self, kdata, cost_calc_methods='amount'):
        self.cm_df = calc_CM(kdata)
        self.pricelist = self.cm_df.columns
        self.avg_price = dict()
        self.present_price = kdata.close.iloc[len(kdata.close) - 1]
        self.cm_distribution_dict = dict()
        self.dist_df = self.calc_all_cm_distribution()
        if cost_calc_methods == 'amount':
            self.avg_cost_line = np.divide(kdata['amount'].values, kdata['volume'].values)
        else:
            self.avg_cost_line = (kdata['open'].values + kdata['high'].values + kdata['low'].values + kdata[
                'close'].values) / 4
        nan_val = np.isnan(self.avg_cost_line)
        for i in range(len(nan_val)):
            if nan_val[i]:
                self.avg_cost_line[i] = kdata['close'].values[i]

    def reindex(self, times=6):
        self.cm_df.index = np.arange(len(self.cm_df)) * times

    def calc_all_cm_distribution(self):  # 约耗时0.2s
        tmp_cm = self.cm_df
        length = len(tmp_cm)
        distribution = np.zeros(tmp_cm.shape)
        k_volume = np.array(tmp_cm.sum(axis=1))
        tmp_cm = tmp_cm.values
        all_volume = tmp_cm.sum()
        tmp_index = 1
        distribution[0] = tmp_cm[0]  # 填充初始行
        tmp_volume = tmp_cm[0].sum()
        while tmp_index < length:
            if tmp_volume < all_volume / 2.618:
                tmp_volume += k_volume[tmp_index]
                distribution[tmp_index] = tmp_cm[tmp_index] + distribution[tmp_index - 1]
                tmp_index += 1
            else:
                ratio = distribution[tmp_index - 1] / distribution[tmp_index - 1].sum()
                distribution[tmp_index] = distribution[tmp_index - 1] - tmp_cm[tmp_index].sum() * ratio + tmp_cm[
                    tmp_index]
                tmp_index += 1
        return pd.DataFrame(data=distribution, index=self.cm_df.index, columns=self.cm_df.columns)

    def calc_cm_distribution(self, start_time, end_time, cm_exchange=False):
        if not cm_exchange:
            tmp_cm = self.cm_df[(self.cm_df.index >= start_time) & (self.cm_df.index <= end_time)].values
            vol_list = tmp_cm.sum(axis=0)  # 逐行相加
            i = 0
            j = -1
            vol_list_len = len(vol_list)
            while i < vol_list_len and vol_list[i] < 10000:
                i += 1
            while j >= -vol_list_len and vol_list[j] < 10000:
                j -= 1
            price_list, vol_list = self.cm_df.columns[i:j], vol_list[i:j]
        else:
            price_list = self.cm_df.columns
            vol_list = self.dist_df[self.dist_df.index == end_time].values
            i = 0
            j = -1
            vol_list = np.array(vol_list)
            vol_list_len = len(vol_list)
            while i < vol_list_len and vol_list[0][i] < 10000:  # vol_list是一个只有一行的二维数组，因此要加个0
                i += 1
            while j >= -vol_list_len and vol_list[0][j] < 10000:
                j -= 1
            price_list, vol_list = price_list[i:j], vol_list[0][i:j]
        return np.array(price_list), vol_list

    def show(self):
        lst_vol = self.cm_df.sum()
        print(self.pricelist)
        print(lst_vol.values)
        # 测试画图
        fig, ax1 = plt.subplots()
        ax1.barh(self.pricelist, lst_vol, height=1 / (self.pricelist[-1] - self.pricelist[0]) / 100)
        plt.savefig('test.jpg')
        plt.show()

    def put_avg_price(self, name, avg_price):
        self.avg_price[name] = avg_price

    def get_avg_price(self, name):
        try:
            p = self.avg_price[name]
            return p
        except KeyError:
            print("wrong name")

    def put_cm_distribution(self, name, price_list, vol_list):
        """

        :param vol_list:
        :param price_list:
        :param name: 4type hightolow,lowtonow,begintonow,begintolow
        """
        self.cm_distribution_dict[name] = (price_list, vol_list)

    def get_cm_distribution(self, name):
        try:
            result = self.cm_distribution_dict[name]
            return result
        except KeyError:
            print("wrong name")

    def get_avg_cost_ma(self, days=None, methods='EMA'):  # 约耗时0.007s
        if days is None:
            amount = self.dist_df.values.dot(self.dist_df.columns.values.T)
            volume = self.dist_df.values.sum(axis=1)  # 逐列相加
            avg_cost = amount / volume
        else:
            if methods == 'EMA':
                avg_cost = Indicators.EMA(self.avg_cost_line, period=days * 48)
            else:
                avg_cost = Indicators.MA(self.avg_cost_line, period=days * 48)
        return avg_cost

    def get_multi_ma(self, methods='EMA'):
        ma3 = self.get_avg_cost_ma(days=3, methods=methods)
        ma9 = self.get_avg_cost_ma(days=9, methods=methods)
        ma14 = self.get_avg_cost_ma(days=14, methods=methods)
        ma28 = self.get_avg_cost_ma(days=28, methods=methods)
        ma60 = self.get_avg_cost_ma(days=60, methods=methods)
        ma120 = self.get_avg_cost_ma(days=120, methods=methods)
        short = ma3 * 0.07 + ma9 * 0.21 + ma14 * 0.36 + ma28 * 0.36
        mid = ma14 * 0.19 + ma28 * 0.31 + ma60 * 0.5
        long = ma28 * 0.19 + ma60 * 0.31 + ma120 * 0.5
        return short, mid, long

    @staticmethod
    def get_avg_cost(pricelist, vollist):
        all_amount = (pricelist * vollist).sum()
        all_vol = vollist.sum()
        return all_amount / all_vol

    def get_winner_rate(self):
        pricelist, vollist = self.get_cm_distribution('begintonow')
        all_volume = vollist.sum()
        tmp_pricelist = pricelist[pricelist <= self.present_price]
        tmp_vollist = vollist[:len(tmp_pricelist)]
        win_volume = tmp_vollist.sum()
        winner_rate = win_volume / all_volume
        return winner_rate
