from VisionQuant.utils.Params import OrderLifeTime, OrderStatus


class Order:
    def __init__(self, order_type, order_code, order_price=None, order_stock_count=None, order_life_time=None):
        self.status = OrderStatus.NEW
        self.order_id = None
        self.account_token = None
        self.type = order_type
        self.code = order_code
        self.price = order_price
        self.stock_count = order_stock_count
        self.remain_stock_count = order_stock_count
        if order_life_time is None:
            self.life_time = OrderLifeTime.UNITLNEXTBAR
        else:
            self.life_time = order_life_time
