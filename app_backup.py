from flask import Flask, request, redirect, render_template, jsonify
from portfolio import Portfolio
import yfinance as yf
import json
from datetime import datetime

app = Flask(__name__)

# Create portfolio
portfolio = Portfolio(10000)
portfolio.load()


# Get live stock price
def get_live_price(symbol):

    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")

    if not data.empty:
        return float(data["Close"].iloc[-1])

    return 0

# -------------------------
# TRANSACTION HISTORY
# -------------------------

def load_transactions():

    try:

        with open("transactions.json", "r") as f:
            return json.load(f)

    except:

        return []


def save_transaction(transaction):

    transactions = load_transactions()

    transactions.append(transaction)

    with open("transactions.json", "w") as f:

        json.dump(
            transactions,
            f,
            indent=4
        )
# -------------------------
# BUY STOCK
# -------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    # Buy stock
    if request.method == "POST":

        name = request.form["name"].upper()
        quantity = int(request.form["quantity"])

        price = get_live_price(name)

        if price == 0:
            return "Stock not found"

        portfolio.buy_stock(name, price, quantity)
        save_transaction({

    "type": "BUY",

    "name": name,

    "quantity": quantity,

    "price": round(price, 2),

    "total": round(price * quantity, 2),

    "date": datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

})
        portfolio.save()

        return redirect("/")


    # Display portfolio
    stock_data = []
    total_stock_value = 0


    for stock in portfolio.stocks.values():

        # Get current live price
        live_price = get_live_price(stock.name)

        # Current value
        value = live_price * stock.quantity

        total_stock_value += value


        # Original investment
        investment = stock.buy_price * stock.quantity


        # Profit / Loss
        profit = value - investment


        # Percentage profit / loss
        if investment != 0:
            percentage = (profit / investment) * 100
        else:
            percentage = 0


        stock_data.append({

            "name": stock.name,

            "quantity": stock.quantity,

            "value": round(value, 2),

            "profit": round(profit, 2),

            "percentage": round(percentage, 2)

        })


    # Total portfolio value
    total_value = portfolio.balance + total_stock_value


    return render_template(

        "index.html",

        balance=round(portfolio.balance, 2),

        stocks=stock_data,

        total=round(total_value, 2)

    )


# -------------------------
# SELL STOCK
# -------------------------

@app.route("/sell", methods=["POST"])
def sell():

    name = request.form["name"].upper()

    quantity = int(
        request.form["quantity"]
    )

    price = get_live_price(name)

    success = portfolio.sell_stock(
        name,
        quantity
    )

    if success:

        save_transaction({

            "type": "SELL",

            "name": name,

            "quantity": quantity,

            "price": round(price, 2),

            "total": round(
                price * quantity,
                2
            ),

            "date": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        })

        portfolio.save()

    return redirect("/")

@app.route("/transactions")
def transactions():

    history = load_transactions()

    return render_template(
        "transactions.html",
        transactions=history
    )
# -------------------------
# PORTFOLIO ALLOCATION
# -------------------------

@app.route("/allocation")
def allocation():

    labels = []
    values = []

    for stock in portfolio.stocks.values():

        live_price = get_live_price(stock.name)

        value = live_price * stock.quantity

        labels.append(stock.name)
        values.append(round(value, 2))

    # Add cash balance
    if portfolio.balance > 0:

        labels.append("Cash")
        values.append(round(portfolio.balance, 2))

    return jsonify({
        "labels": labels,
        "values": values
    })


# -------------------------
# STOCK CHART
# -------------------------

@app.route("/chart/<symbol>")
def chart(symbol):

    symbol = symbol.upper()


    ticker = yf.Ticker(symbol)

    data = ticker.history(period="1mo")


    if data.empty:

        return jsonify({

            "dates": [],

            "prices": []

        })


    dates = data.index.strftime("%Y-%m-%d").tolist()

    prices = data["Close"].astype(float).tolist()


    return jsonify({

        "dates": dates,

        "prices": prices

    })


# -------------------------
# RUN APP
# -------------------------

if __name__ == "__main__":

    app.run(debug=True)