import uuid

from VisionQuant.Accounts.AccountBase import AccountBase
from VisionQuant.utils.Params import OrderType


class BackTradeAccount(AccountBase):
    def __init__(self, init_moeny=None, commission=None, risk_mng=None, min_risk_rate=2, stop_rate=0.02):
        super().__init__(init_moeny, commission)
        self.account_token = 'test'
        self.frozen_money = 0
        if risk_mng is not None:
            self.risk_mng = risk_mng(min_risk_rate, stop_rate)
        else:
            self.risk_mng = None

    def set_commisson(self, commission):
        self.commission = commission

    def set_init_money(self, init_money):
        self.avl_money = init_money

    def set_risk_manager(self, func):
        self.risk_mng = func()

    def get_max_avl_stock_cnt(self, price, rate):
        stk_count = (self.avl_money * rate) / (price * (1 + self.commission))
        if stk_count < 100:
            return 0
        else:
            return int(stk_count)

    def get_all_capital(self):
        return self.avl_money + self.frozen_money + self.risk_mng.capital_mng.get_capital_amount()

    def get_stock_capital(self):
        return self.risk_mng.capital_mng.get_capital_amount()

    def process_analyze_result(self, result):
        tmp_order = self.risk_mng.process_ana_result(result, self)
        if tmp_order.type != OrderType.EMPTY:
            return self.send_order(tmp_order)
        else:
            return None

    def send_order(self, order):
        order.order_id = str(uuid.uuid4())
        order.account_token = self.account_token
        if order.type == OrderType.BUY:
            self.avl_money -= order.price * order.stock_count * (1 + self.commission)
            self.frozen_money += order.price * order.stock_count * (1 + self.commission)
        return order

    def recv_order_result(self, order_result_list):
        for order_result in order_result_list:
            if order_result.type == OrderType.CELL and \
                    self.risk_mng.capital_mng.search_capital(order_result.code) is not None:
                self.avl_money += order_result.final_price * order_result.stock_count
                self.risk_mng.process_order_result(order_result)
            elif order_result.type == OrderType.BUY:
                self.frozen_money -= order_result.final_price * order_result.stock_count * (1 + self.commission)
                self.risk_mng.process_order_result(order_result)
            elif order_result.type == OrderType.CANCEL_BUY:
                self.avl_money += order_result.final_price * order_result.stock_count * (1 + self.commission)
                self.frozen_money -= order_result.final_price * order_result.stock_count * (1 + self.commission)
            elif order_result.type == OrderType.CANCEL_SELL:
                self.risk_mng.process_order_result(order_result)

    def market_close_settled(self):
        self.risk_mng.capital_mng.market_close_settled()

    def show(self):
        capital_amount = self.risk_mng.capital_mng.get_capital_amount()
        print("资产持有情况")
        self.risk_mng.capital_mng.show()
        print('当前可用资金: {:.2f}, 冻结资金: {:.2f}, 当前资产: {:.2f}, 当前总资产: {:.2f}'.format(
            self.avl_money, self.frozen_money, capital_amount, self.get_all_capital()))
