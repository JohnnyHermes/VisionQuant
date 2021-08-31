class AccountBase(object):
    def __init__(self, avl_money, commission):
        self.commission = commission
        self.avl_money = avl_money


class OrderResult(object):
    def __init__(self, order_type, code: str, final_price, stock_count):
        self.type = order_type
        self.code = code
        self.final_price = final_price
        self.stock_count = stock_count
