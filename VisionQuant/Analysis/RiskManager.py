from VisionQuant.Accounts.Order import Order
from VisionQuant.Analysis.StrategyBase import AnalyzeResult
from VisionQuant.utils.Params import OrderType, OrderLifeTime


class CapitalBase(object):
    def __init__(self, order_result):
        self.code = order_result.code
        self._present_price = order_result.final_price
        self._cost_price = order_result.final_price
        self._avl_stock_count = None
        self._queued_stock_count = 0
        self._cost_capital = None
        self._now_capital = self._cost_capital

    def update_present_price(self, pp):
        self._present_price = pp
        self._update_now_capital()

    def _update_now_capital(self):
        self._now_capital = self.get_all_stock_count() * self._present_price

    def get_now_capital(self):
        return self._now_capital

    def get_cost_capital(self):
        return self._cost_capital

    def get_cost_price(self):
        return self._cost_price

    def get_avl_stock_count(self):  # 如果有每日交易限制（A股），则获取的是可交易的数量
        return self._avl_stock_count

    def get_all_stock_count(self):
        return self._avl_stock_count + self._queued_stock_count

    def market_close_settled(self):
        pass

    def freeze_stock(self, stock_count):
        self._queued_stock_count += stock_count
        self._avl_stock_count -= stock_count

    def update_capital(self, order_result):
        if order_result.type == OrderType.CELL:
            self._queued_stock_count -= order_result.stock_count
            self._cost_capital -= order_result.final_price * order_result.stock_count
            self._update_now_capital()
            if self.get_all_stock_count() == 0:
                return False
            else:
                return True
        elif order_result.type == OrderType.BUY:
            self._avl_stock_count += order_result.stock_count
            self._cost_capital += order_result.final_price * order_result.stock_count
            self._cost_price = self._cost_capital / self.get_all_stock_count()
            self._update_now_capital()
            return True
        elif order_result.type == OrderType.CANCEL_SELL:
            self._avl_stock_count += order_result.stock_count
            self._queued_stock_count -= order_result.stock_count
            self._update_now_capital()
            return True
        else:
            raise TypeError("错误的order_result.type")


class Capital(CapitalBase):
    def __init__(self, order_result):
        super().__init__(order_result)
        self._stock_count = order_result.stock_count
        self._cost_capital = order_result.final_price * order_result.stock_count
        self._now_capital = self._cost_capital


class AshareCapital(CapitalBase):
    def __init__(self, order_result):
        super().__init__(order_result)
        self._avl_stock_count = 0
        self._frozen_stock_count = order_result.stock_count
        self._cost_capital = order_result.final_price * order_result.stock_count
        self._now_capital = self._cost_capital

    def get_all_stock_count(self):
        return self._avl_stock_count + self._frozen_stock_count + self._queued_stock_count

    def update_capital(self, order_result):
        if order_result.type == OrderType.CELL:
            self._queued_stock_count -= order_result.stock_count
            self._cost_capital -= order_result.final_price * order_result.stock_count
            self._update_now_capital()
            if self.get_all_stock_count() == 0:
                return False
            else:
                return True
        elif order_result.type == OrderType.BUY:
            self._frozen_stock_count += order_result.stock_count
            self._cost_capital += order_result.final_price * order_result.stock_count
            self._cost_price = self._cost_capital / self.get_all_stock_count()
            self._update_now_capital()
            return True
        elif order_result.type == OrderType.CANCEL_SELL:
            self._avl_stock_count += order_result.stock_count
            self._queued_stock_count -= order_result.stock_count
            self._update_now_capital()
            return True
        else:
            raise TypeError("错误的order_result.type")

    def market_close_settled(self):
        self._avl_stock_count += self._frozen_stock_count
        self._frozen_stock_count = 0


class CapitalManager(object):
    def __init__(self, capital):
        self.capital_dict = dict()
        self.capital = capital

    def process_order_result(self, order_result):
        if self.search_capital(order_result.code) is not None:
            self._update_capital(order_result)
        else:
            self._add_capital(order_result)

    def _add_capital(self, order_result):
        self.capital_dict[order_result.code] = self.capital(order_result)

    def _update_capital(self, order_result):
        flag = self.search_capital(order_result.code).update_capital(order_result)
        if not flag:
            self._remove_capital(order_result.code)

    def _remove_capital(self, code: str):
        del self.capital_dict[code]

    def search_capital(self, code: str):
        if code in self.capital_dict:
            return self.capital_dict[code]
        else:
            return None

    def update_present_price(self, code: str, price):
        self.search_capital(code).update_present_price(price)

    def get_capital_amount(self):
        amount = 0
        for k, capital in self.capital_dict.items():
            amount += capital.get_now_capital()
        return amount

    def get_cost_capital(self, code: str):
        return self.search_capital(code).get_cost_capital()

    def show(self):
        for k, capital in self.capital_dict.items():
            print('代码:{}, 成本价: {:.2f}, 持股数: {}, 可用股数: {}, 资产: {:.2f}, 盈亏: {:.2f}'.format(
                capital.code, capital.get_cost_price(), capital.get_all_stock_count(),
                capital.get_avl_stock_count(), capital.get_now_capital(),
                capital.get_now_capital() - capital.get_cost_capital()
            ))

    def market_close_settled(self):
        for k, capital in self.capital_dict.items():
            capital.market_close_settled()


class RiskManager(object):
    def __init__(self, min_risk_rate=1.5, stop_rate=0.02):
        self.stop_rate = stop_rate
        self.min_risk_rate = min_risk_rate
        self.result_log = []
        self.capital_mng = CapitalManager(AshareCapital)
        self.stop_price_dict = dict()
        self.target_price_dict = dict()
        self.stop_price_log = []
        self.target_price_log = []
        self.cost_price_log = []
        self.risk_rate_log = []

    def process_ana_result(self, result: AnalyzeResult, account):
        # self.result_log.append(result)
        # print(result.stop_p,result.stop_p1)
        if self.capital_mng.search_capital(result.code) is not None:
            # 更新Capital对象中的present_price
            self.capital_mng.update_present_price(result.code, result.present_price)

            # 更新目标止盈价
            if result.target_p > self.target_price_dict[result.code]:
                self.target_price_dict[result.code] = result.target_p
            # 获取当前成本价
            cost_price = self.capital_mng.search_capital(result.code).get_cost_price()
            # 超过成本线，考虑提高止损价，以期减少亏损
            if result.present_price >= cost_price:
                if result.present_price >= cost_price * (1 + self.stop_rate):  # 若超过盈利底线，先提高至成本价
                    self.stop_price_dict[result.code] = max(self.stop_price_dict[result.code], cost_price)
                # 更新止损价
                self.stop_price_dict[result.code] = max(result.stop_p, result.stop_p1,
                                                        self.stop_price_dict[result.code])
                # self.stop_price_dict[result.code] = max(result.stop_p, self.stop_price_dict[result.code])
            else:  # 处于亏损状态
                self.stop_price_dict[result.code] = max(result.stop_p, self.stop_price_dict[result.code])
            self.cost_price_log.append(cost_price)
            self.stop_price_log.append(self.stop_price_dict[result.code])
            self.target_price_log.append(self.target_price_dict[result.code])
            # print(self.stop_price_dict[result.code] > result.present_price)
            risk_rate = (result.target_p - result.exp_final_p) / (result.exp_final_p - result.stop_p)
            self.risk_rate_log.append(risk_rate)
            # 如果到达止损价，卖出
            if self.capital_mng.search_capital(result.code).get_avl_stock_count() > 0 and \
                    result.present_price <= self.stop_price_dict[result.code]:
                if risk_rate >= self.min_risk_rate:
                    rate = self.stop_rate * (1 + account.commission) / (1 - result.stop_p / result.exp_final_p)
                    min_rate = self.capital_mng.get_cost_capital(result.code) / account.get_all_capital()
                    if rate >= min_rate:
                        return Order(order_type=OrderType.EMPTY, order_code=result.code)
                    else:
                        order_stock = self.capital_mng.search_capital(result.code).get_avl_stock_count() - \
                                      account.get_max_avl_stock_cnt(result.exp_final_p, rate)
                        # self.stop_price_dict[result.code] = max(result.stop_p, cost_price)
                else:
                    order_stock = self.capital_mng.search_capital(result.code).get_avl_stock_count()
                order_type = OrderType.CELL
                order_life_time = OrderLifeTime.IMMEDIATELY
                order_code = result.code
                order_price = (self.stop_price_dict[result.code] * 0.618 + result.present_price * 0.382)  # todo:可修改
                # order_stock = self.capital_mng.search_capital(result.code).get_avl_stock_count()
                self.capital_mng.search_capital(result.code).freeze_stock(order_stock)
                print("触发风控机制")
                return Order(order_type, order_code, order_price, order_stock, order_life_time)

            # 追加买入条件计算
            if risk_rate < self.min_risk_rate or \
                    (result.target_p / result.exp_final_p - 1) < self.min_risk_rate * self.stop_rate:
                return Order(order_type=OrderType.EMPTY, order_code=result.code)
            else:
                rate = self.stop_rate * (1 + account.commission) / (1 - result.stop_p / result.exp_final_p)
                # if (result.target_p / result.exp_final_p - 1) > 0.15:  # >0.15认为是突破了，放松止损率以期获取更多利润
                #     rate *= 2
                # 计算当前的capital_rate
                min_rate = self.capital_mng.get_cost_capital(result.code) / account.get_all_capital()
                if rate > 1:
                    rate = 1
                elif rate <= 0 or rate < min_rate:
                    return Order(order_type=OrderType.EMPTY, order_code=result.code)
                else:
                    rate = rate - min_rate
                order_stock = account.get_max_avl_stock_cnt(result.exp_final_p, rate)
                if order_stock == 0:
                    return Order(order_type=OrderType.EMPTY, order_code=result.code)
                else:
                    order_type = OrderType.BUY
                    order_code = result.code
                    order_price = result.exp_final_p
                    return Order(order_type, order_code, order_price, order_stock)
        else:
            if result.code in self.stop_price_dict:
                del self.stop_price_dict[result.code]
                del self.target_price_dict[result.code]
            self.stop_price_log.append(result.stop_p)
            self.target_price_log.append(result.target_p)
            self.cost_price_log.append(result.stop_p)
            # 买入条件计算
            risk_rate = (result.target_p - result.exp_final_p) / (result.exp_final_p - result.stop_p)
            self.risk_rate_log.append(risk_rate)
            if risk_rate < self.min_risk_rate:
                return Order(order_type=OrderType.EMPTY, order_code=result.code)
            else:
                rate = self.stop_rate * (1 + account.commission) / (1 - result.stop_p / result.exp_final_p)
                if rate > 1:
                    rate = 1
                elif rate <= 0:
                    return Order(order_type=OrderType.EMPTY, order_code=result.code)
                order_stock = account.get_max_avl_stock_cnt(result.exp_final_p, rate)
                if order_stock == 0:
                    return Order(order_type=OrderType.EMPTY, order_code=result.code)
                else:
                    order_type = OrderType.BUY
                    order_code = result.code
                    order_price = result.exp_final_p
                    self.target_price_dict[result.code] = result.target_p
                    self.stop_price_dict[result.code] = result.stop_p
                    return Order(order_type, order_code, order_price, order_stock)

    def process_order_result(self, order_result):
        self.capital_mng.process_order_result(order_result)


if __name__ == '__main__':
    pass
