import json
from stock import Stock

class Portfolio:
    def __init__(self, balance):
        self.balance = balance
        self.stocks = {}

    def buy_stock(self, name, price, quantity):
        cost = price * quantity

        if cost > self.balance:
            print("Not enough money!")
            return

        self.balance -= cost

        if name in self.stocks:
            self.stocks[name].buy(quantity)
        else:
            stock = Stock(name, price)
            stock.buy(quantity)
            self.stocks[name] = stock

        print(f"Bought {quantity} shares of {name}")
    def sell_stock(self, name, quantity):
        if name in self.stocks:

            stock = self.stocks[name]

            if stock.quantity >= quantity:

                sell_value = stock.price * quantity

                stock.quantity -= quantity
                self.balance += sell_value

                if stock.quantity == 0:
                    del self.stocks[name]

                return True

        return False
    def show_portfolio(self):
        print("\n--- Portfolio ---")
        print(f"Balance: £{self.balance}")

        print("\nStock      | Shares | Value")
        print("-" * 30)

        total = self.balance

        for stock in self.stocks.values():
            value = stock.value()
            total += value

            print(f"{stock.name:10} | {stock.quantity:5} shares | £{value}")

        print("-" * 30)
        print(f"Total value: £{total}")

    def save(self):
        data = {
            "balance": self.balance,
            "stocks": {
                name: {
                    "price": stock.price,
                    "quantity": stock.quantity
                }
                for name, stock in self.stocks.items()
            }
        }

        with open("data.json", "w") as f:
            json.dump(data, f)

    def load(self):
        try:
            with open("data.json", "r") as f:
                data = json.load(f)

                self.balance = data["balance"]

                for name, info in data["stocks"].items():
                    stock = Stock(name, info["price"])
                    stock.quantity = info["quantity"]
                    self.stocks[name] = stock

        except:
            print("No saved data found")