import time

import numpy as np

from VisionQuant.Accounts.AccountBase import OrderResult
from VisionQuant.Accounts.BackTradeAccount import BackTradeAccount
from VisionQuant.Analysis.RiskManager import RiskManager
from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import Freq, OrderStatus, OrderLifeTime, OrderType
import datetime
from VisionQuant.Analysis.Relativity.relativity_old import Relativity
from VisionQuant.Engine.AnalyzeEngine import AnalyzeEngine


class BackTrader:
    def __init__(self, account):
        self.account = account
        self.bt_start_time = None
        self.bt_end_time = None
        self.step = None
        self.code = None
        self.data_struct = None
        self.kdata_start_time = None
        self.present_price = 0.0
        self.high_price = 0.0
        self.low_price = 0.0
        self.volume = 0
        self.timestamp = None
        self.order_list = []
        self.order_list_log = []
        self.capital_log = []
        self.avl_money_log = []
        self.capital_rate_log = []

    def set_time(self, start_time, end_time, step):
        self.bt_start_time = start_time
        self.bt_end_time = end_time
        self.step = self._get_time_step(step)

    def set_code(self, code):
        self.code = code

    def set_data(self, datastruct):
        self.data_struct = datastruct
        self.kdata_start_time = self.data_struct.get_kdata('5').get_start_time()
        self.timestamp = self.data_struct.get_kdata('5').data_struct['time'].values
        self.timestamp = self.timestamp[np.where(self.bt_start_time <= self.timestamp)]
        self.timestamp = self.timestamp[np.where(self.timestamp <= self.bt_end_time)]

    def process_order(self, order=None, at_last=False):
        order_result_list = []
        if order is None:
            i = 0
            while i < len(self.order_list):
                if self.order_list[i].status in (OrderStatus.QUEUED, OrderStatus.SUCCESS_PART):
                    if at_last:
                        order = self.order_list.pop(i)
                        order_result = self._process_order(order)
                        if order_result is not None:
                            order_result_list.append(order_result)
                            order.remain_stock_count -= order_result.stock_count
                            if order.remain_stock_count > 0:
                                order.status = OrderStatus.SUCCESS_PART
                                self.order_list_log.append(order)
                                order.status = OrderStatus.FAILED
                                order_result_list.append(self._process_order(order))
                            else:
                                order.status = OrderStatus.SUCCESS_ALL
                                self.order_list_log.append(order)
                        else:
                            order.status = OrderStatus.FAILED
                            self.order_list_log.append(order)
                            order_result_list.append(self._process_order(order))
                        continue
                    else:
                        if self.order_list[i].life_time in [OrderLifeTime.UNTILEND, OrderLifeTime.UNTILCANCEL]:
                            order_result = self._process_order(self.order_list[i])
                            if order_result is not None:
                                self.order_list[i].remain_stock_count -= order_result.stock_count
                                if self.order_list[i].remain_stock_count > 0:
                                    self.order_list[i].status = OrderStatus.SUCCESS_PART
                                else:
                                    self.order_list[i].status = OrderStatus.SUCCESS_ALL
                                order_result_list.append(order_result)
                        elif self.order_list[i].life_time == OrderLifeTime.UNITLNEXTBAR:
                            order = self.order_list.pop(i)
                            order_result = self._process_order(order)
                            if order_result is not None:
                                order_result_list.append(order_result)
                                order.remain_stock_count -= order_result.stock_count
                                if order.remain_stock_count > 0:
                                    order.status = OrderStatus.SUCCESS_PART
                                    self.order_list_log.append(order)
                                    order.status = OrderStatus.FAILED
                                    order_result_list.append(self._process_order(order))
                                else:
                                    order.status = OrderStatus.SUCCESS_ALL
                                    self.order_list_log.append(order)
                            else:
                                if order.status != OrderStatus.SUCCESS_PART:
                                    self.order_list_log.append(order)
                                    order.status = OrderStatus.FAILED
                                    order_result_list.append(self._process_order(order))
                                else:
                                    order.status = OrderStatus.FAILED
                                    self.order_list_log.append(order)
                                    order_result_list.append(self._process_order(order))
                            continue
                elif self.order_list[i].status in (OrderStatus.SUCCESS_ALL, OrderStatus.FAILED):
                    self.order_list_log.append(self.order_list.pop(i))
                    continue
                else:
                    self.order_list_log.append(self.order_list.pop(i))
                    continue
                i += 1
        else:
            order.status = OrderStatus.QUEUED
            if order.life_time == OrderLifeTime.IMMEDIATELY:
                order_result = self._process_order(order)
                if order_result is not None:
                    order_result_list.append(order_result)
                    order.remain_stock_count -= order_result.stock_count
                    if order.remain_stock_count > 0:
                        order.status = OrderStatus.SUCCESS_PART
                        self.order_list_log.append(order)
                        order.status = OrderStatus.FAILED
                        order_result_list.append(self._process_order(order))
                    else:
                        order.status = OrderStatus.SUCCESS_ALL
                        self.order_list_log.append(order)
                else:
                    order.status = OrderStatus.FAILED
                    self.order_list_log.append(order)
                    order_result_list.append(self._process_order(order))
            elif order.life_time == OrderLifeTime.UNITLNEXTBAR:
                order_result = self._process_order(order)
                if order_result is not None:
                    order_result_list.append(order_result)
                    order.remain_stock_count -= order_result.stock_count
                    if order.remain_stock_count > 0:
                        order.status = OrderStatus.SUCCESS_PART
                        self.order_list.append(order)
                    else:
                        order.status = OrderStatus.SUCCESS_ALL
                        self.order_list_log.append(order)
                else:
                    self.order_list.append(order)
            else:
                self.order_list.append(order)
        return order_result_list

    def _process_order(self, order):
        """
        :param order:
        :return:
        """
        if order.status != OrderStatus.FAILED:
            if order.type == OrderType.BUY:
                if self.low_price <= order.price <= self.high_price:
                    max_volume = self.volume * 0.5
                    if order.remain_stock_count > max_volume:
                        stock_count = max_volume
                    else:
                        stock_count = order.remain_stock_count
                    return OrderResult(order_type=order.type,
                                       code=order.code,
                                       final_price=order.price,
                                       stock_count=stock_count)
                else:
                    return None
            elif order.type == OrderType.CELL:
                max_volume = self.volume * 0.5
                if order.remain_stock_count > max_volume:
                    stock_count = max_volume
                else:
                    stock_count = order.remain_stock_count
                return OrderResult(order_type=order.type,
                                   code=order.code,
                                   final_price=order.price,
                                   stock_count=stock_count)
        elif order.status == OrderStatus.FAILED:
            if order.type == OrderType.BUY:
                order_type = OrderType.CANCEL_BUY
            elif order.type == OrderType.CELL:
                order_type = OrderType.CANCEL_SELL
            else:
                raise TypeError("_process_order函数: 错误的order.type类型")
            return OrderResult(order_type=order_type,
                               code=order.code,
                               final_price=order.price,
                               stock_count=order.remain_stock_count)
        else:
            raise TypeError("_process_order函数: 错误的order.status类型")

    def start_backtest(self, strategy=Relativity):
        analyze_engine = AnalyzeEngine()
        # time_stamp = self.timestamp[2::3]
        time_stamp = self.timestamp
        for bt_now_time in time_stamp:
            # fliter出新的kdatastruct
            tmp_data = self.data_struct.filter(key='time', start=self.kdata_start_time,
                                               end=bt_now_time, is_reset_index=True)
            print(TimeTool.time_to_str(tmp_data.get_kdata('5').get_last_time()))
            # 运行策略，更新数据
            tmp_code = self.code.copy()
            tmp_code.end_time = bt_now_time
            analyze_engine.register_strategy(strategy=strategy, codes=self.code, local_data=tmp_data)
            _, self.present_price, self.high_price, self.low_price, self.volume = \
                tmp_data.get_kdata(self.code.frequency).get_last_bar_values()
            analyze_result = analyze_engine.run_strategy(tmp_code)
            # 处理上一个bar遗留下来的order
            order_result = self.process_order()
            # 回传给account进行处理
            self.account.recv_order_result(order_result)
            # 看是否能够生成order
            order = self.account.process_analyze_result(analyze_result)
            if order is not None:
                # 生成了order，处理该order
                order_result = self.process_order(order)
                self.account.recv_order_result(order_result)

            # 如果收盘，清理order_list
            if self._is_at_end_time(bt_now_time):
                order_result = self.process_order(at_last=True)
                self.account.recv_order_result(order_result)
                self.account.market_close_settled()
            # 收尾，展示资产数
            self.account.show()
            self.capital_log.append(self.account.get_all_capital())
            self.capital_rate_log.append(self.account.get_stock_capital() / self.account.get_all_capital())
            # self.avl_money_log.append(self.account.avl_money)

    @staticmethod
    def _is_at_end_time(current_time):
        dt = TimeTool.npdt64_to_dt(current_time)
        if dt.hour == 15 and dt.minute == 0:
            return True
        else:
            return False

    @staticmethod
    def _get_time_step(step):
        if step == Freq.MIN5:
            return datetime.timedelta(minutes=5)
        elif step == Freq.DAY:
            return datetime.timedelta(days=1)
        else:
            return datetime.timedelta(minutes=5)


if __name__ == '__main__':
    from VisionQuant.DataCenter.CodePool import get_ashare_stock_dict
    from VisionQuant.utils.Params import MarketType
    import matplotlib.pyplot as plt
    import gc
    import pickle
    start_time = TimeTool.time_standardization('2021-1-1')
    end_time = TimeTool.time_standardization('2021-8-30')

    code_list = ['399006', '000300',
                 '002382', '601101', '000911', '002340', '000150', '600036', '600958',
                 '601678', '600733', '002248', '600519', '002460']
    code_dict = get_ashare_stock_dict(code_list, start_time='2020-1-1')
    # code_list = get_ashare_stock_list(['999999'], start_time='2020-1-1')
    fig = plt.figure(figsize=(16, 18))
    grid = plt.GridSpec(18, 1)
    for test_code in code_dict.values():
        if test_code.market in [MarketType.Ashare.SH.INDEX, MarketType.Ashare.SH.ETF,
                                MarketType.Ashare.SZ.INDEX, MarketType.Ashare.SZ.ETF]:
            stop_rate = 0.02
        else:
            stop_rate = 0.03
        t1 = time.time()
        test_account = BackTradeAccount(init_moeny=10000000, commission=0.00025,
                                        risk_mng=RiskManager, min_risk_rate=2, stop_rate=stop_rate)
        test_bt = BackTrader(test_account)
        test_bt.set_time(start_time=start_time,
                         end_time=end_time, step=Freq.MIN5)
        data_server = DataServer()
        test_data = data_server.get_data(codes=test_code)
        test_bt.set_code(test_code)
        test_bt.set_data(test_data)
        test_bt.start_backtest(strategy=Relativity)
        t2 = time.time()
        print(t2 - t1)
        # 储存一下
        time_str = "{}_{}_{}_backtest".format(test_code.code, TimeTool.time_to_str(start_time, fmt='%Y%m%d'),
                                              TimeTool.time_to_str(end_time, fmt='%Y%m%d'))
        with open(time_str + '.pkl', 'wb') as f:
            pickle.dump(test_bt, f)
        price_ax = plt.subplot(grid[0:9, 0:1])
        plt.title(time_str)
        close = np.array(
            test_bt.data_struct.get_kdata('5').filter(key='time', start=start_time, end=end_time).data_struct['close'].values)
        # close = close[2::3]
        tp_log = np.array(test_bt.account.risk_mng.target_price_log)
        sp_log = np.array(test_bt.account.risk_mng.stop_price_log)
        plt.plot(range(len(tp_log)), tp_log, label='tp')
        plt.plot(range(len(sp_log)), sp_log, label='sp')
        plt.plot(range(len(close)), close, label='close')
        plt.legend()
        plt.subplot(grid[9:14, 0:1], sharex=price_ax)
        capitals = np.array(test_bt.capital_log) / test_bt.capital_log[0]
        std_close = close / close[0]
        plt.plot(range(len(std_close)), std_close, label='std_close')
        plt.plot(range(len(capitals)), capitals, label='cpt')
        plt.legend()
        plt.subplot(grid[14:16, 0:1], sharex=price_ax)
        plt.ylim(-0.1, 1.1)
        plt.plot(range(len(test_bt.capital_rate_log)), test_bt.capital_rate_log)
        plt.subplot(grid[16:18, 0:1], sharex=price_ax)
        plt.plot(range(len(test_bt.account.risk_mng.risk_rate_log)), test_bt.account.risk_mng.risk_rate_log)
        plt.savefig(test_code.code + '_result.jpg', dpi=600)
        plt.clf()
        # 清理内存
        del test_account, test_bt, data_server, test_data, close, tp_log, sp_log, capitals, std_close
        gc.collect()

    # plt.show()
