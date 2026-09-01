class Stock:

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

        # Remember buying price
        self.buy_price = price

    def buy(self, amount):
        self.quantity += amount

    def value(self):
        return self.quantity * self.price