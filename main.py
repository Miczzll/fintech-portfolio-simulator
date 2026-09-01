from portfolio import Portfolio
from test_api import get_price

portfolio = Portfolio(10000)
portfolio.load()

while True:
    print("\n1. Buy stock")
    print("2. View portfolio")
    print("3. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        name = input("Stock symbol (e.g. AAPL): ").upper()

        price = get_price(name)

        if price is None:
            print("Invalid stock!")
            continue

        print(f"Current price: £{price}")

        quantity = int(input("Quantity: "))
        portfolio.buy_stock(name, price, quantity)

    elif choice == "2":
        portfolio.show_portfolio()

    elif choice == "3":
        portfolio.save()
        print("Saved. Goodbye!")
        break