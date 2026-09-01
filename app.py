from flask import (
    Flask,
    request,
    redirect,
    render_template,
    jsonify,
    flash
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from portfolio import Portfolio
from stock import Stock

import yfinance as yf
import json
from datetime import datetime


app = Flask(__name__)

# Secret key used for login sessions
app.secret_key = "fintech_simulator_secret_key"


# =========================================================
# FLASK LOGIN
# =========================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


class User(UserMixin):

    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):

    users = load_users()

    if username in users:
        return User(username)

    return None


# =========================================================
# USERS
# =========================================================

def load_users():

    try:

        with open("users.json", "r") as f:
            return json.load(f)

    except:

        return {}


def save_users(users):

    with open("users.json", "w") as f:

        json.dump(
            users,
            f,
            indent=4
        )


# =========================================================
# TRANSACTIONS
# =========================================================

def load_transactions(username):

    try:

        with open(
            f"transactions_{username}.json",
            "r"
        ) as f:

            return json.load(f)

    except:

        return []


def save_transaction(username, transaction):

    transactions = load_transactions(username)

    transactions.append(transaction)

    with open(
        f"transactions_{username}.json",
        "w"
    ) as f:

        json.dump(
            transactions,
            f,
            indent=4
        )


# =========================================================
# PORTFOLIO
# =========================================================

def get_portfolio(username):

    portfolio = Portfolio(10000)

    filename = f"portfolio_{username}.json"

    try:

        with open(filename, "r") as f:

            data = json.load(f)

        portfolio.balance = data["balance"]

        for name, info in data["stocks"].items():

            stock = Stock(
                name,
                info["price"],
                info["quantity"]
            )

            # Restore original buying price
            if "buy_price" in info:
                stock.buy_price = info["buy_price"]

            portfolio.stocks[name] = stock

    except:

        pass

    return portfolio


def save_portfolio(username, portfolio):

    data = {

        "balance": portfolio.balance,

        "stocks": {

            name: {

                "price": stock.price,

                "quantity": stock.quantity,

                "buy_price": stock.buy_price

            }

            for name, stock
            in portfolio.stocks.items()

        }

    }

    with open(
        f"portfolio_{username}.json",
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


# =========================================================
# LIVE STOCK PRICE
# =========================================================

def get_live_price(symbol):

    try:

        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="1d"
        )

        if not data.empty:

            return float(
                data["Close"].iloc[-1]
            )

    except:

        pass

    return 0


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        username = request.form["username"].strip()

        password = request.form["password"]

        users = load_users()

        if username not in users:

            flash(
                "Username or password is incorrect.",
                "error"
            )

            return redirect("/login")

        stored_password = users[username]["password"]

        if check_password_hash(
            stored_password,
            password
        ):

            user = User(username)

            login_user(user)

            return redirect("/")

        flash(
            "Username or password is incorrect.",
            "error"
        )

        return redirect("/login")

    return render_template("login.html")


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":

        username = request.form["username"].strip()

        password = request.form["password"]

        users = load_users()

        if username in users:

            flash(
                "Username already exists.",
                "error"
            )

            return redirect("/register")

        if len(username) < 3:

            flash(
                "Username must be at least 3 characters.",
                "error"
            )

            return redirect("/register")

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "error"
            )

            return redirect("/register")

        users[username] = {

            "password":
                generate_password_hash(password)

        }

        save_users(users)

        # Give every new user £10,000
        portfolio = Portfolio(10000)

        save_portfolio(
            username,
            portfolio
        )

        login_user(
            User(username)
        )

        return redirect("/")

    return render_template("register.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")


# =========================================================
# MAIN DASHBOARD
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
@login_required
def home():

    portfolio = get_portfolio(
        current_user.id
    )

    # =====================================================
    # BUY STOCK
    # =====================================================

    if request.method == "POST":

        name = request.form["name"].upper().strip()

        try:

            quantity = int(
                request.form["quantity"]
            )

        except:

            flash(
                "Please enter a valid quantity.",
                "error"
            )

            return redirect("/")

        # Prevent zero or negative quantities
        if quantity <= 0:

            flash(
                "Quantity must be at least 1.",
                "error"
            )

            return redirect("/")

        # Get live price
        price = get_live_price(name)

        if price == 0:

            flash(
                "Stock not found.",
                "error"
            )

            return redirect("/")

        cost = price * quantity

        # Prevent spending more than balance
        if cost > portfolio.balance:

            flash(
                "You don't have enough money to make this purchase.",
                "error"
            )

            return redirect("/")

        # Buy stock
        portfolio.buy_stock(
            name,
            price,
            quantity
        )

        # Save transaction
        save_transaction(

            current_user.id,

            {

                "type": "BUY",

                "name": name,

                "quantity": quantity,

                "price": round(
                    price,
                    2
                ),

                "total": round(
                    cost,
                    2
                ),

                "date":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

            }

        )

        # Save portfolio
        save_portfolio(
            current_user.id,
            portfolio
        )

        return redirect("/")

    # =====================================================
    # DISPLAY PORTFOLIO
    # =====================================================

    stock_data = []

    total_stock_value = 0

    for stock in portfolio.stocks.values():

        live_price = get_live_price(
            stock.name
        )

        value = (
            live_price *
            stock.quantity
        )

        total_stock_value += value

        # Profit / loss
        buy_price = stock.buy_price

        profit = (
            live_price -
            buy_price
        ) * stock.quantity

        percentage = 0

        if buy_price != 0:

            percentage = (
                (live_price - buy_price)
                / buy_price
            ) * 100

        stock_data.append({

            "name":
                stock.name,

            "quantity":
                stock.quantity,

            "value":
                round(
                    value,
                    2
                ),

            "profit":
                round(
                    profit,
                    2
                ),

            "percentage":
                round(
                    percentage,
                    2
                )

        })

    total_value = (
        portfolio.balance +
        total_stock_value
    )

    return render_template(

        "index.html",

        balance=round(
            portfolio.balance,
            2
        ),

        stocks=stock_data,

        total=round(
            total_value,
            2
        ),

        username=current_user.id

    )


# =========================================================
# SELL STOCK
# =========================================================

@app.route(
    "/sell",
    methods=["POST"]
)
@login_required
def sell():

    portfolio = get_portfolio(
        current_user.id
    )

    name = request.form[
        "name"
    ].upper().strip()

    try:

        quantity = int(
            request.form["quantity"]
        )

    except:

        flash(
            "Please enter a valid quantity.",
            "error"
        )

        return redirect("/")

    # Prevent zero / negative quantities
    if quantity <= 0:

        flash(
            "Quantity must be at least 1.",
            "error"
        )

        return redirect("/")

    # Check stock exists
    if name not in portfolio.stocks:

        flash(
            "You don't own this stock.",
            "error"
        )

        return redirect("/")

    # Check enough shares
    if quantity > portfolio.stocks[name].quantity:

        flash(
            "You don't own enough shares.",
            "error"
        )

        return redirect("/")

    # Get live price
    price = get_live_price(name)

    if price == 0:

        flash(
            "Unable to get the current stock price.",
            "error"
        )

        return redirect("/")

    sell_value = price * quantity

    # Sell
    success = portfolio.sell_stock(
        name,
        quantity
    )

    if success:

        save_transaction(

            current_user.id,

            {

                "type": "SELL",

                "name": name,

                "quantity": quantity,

                "price": round(
                    price,
                    2
                ),

                "total": round(
                    sell_value,
                    2
                ),

                "date":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

            }

        )

        save_portfolio(
            current_user.id,
            portfolio
        )

    return redirect("/")


# =========================================================
# TRANSACTION HISTORY
# =========================================================

@app.route("/transactions")
@login_required
def transactions():

    history = load_transactions(
        current_user.id
    )

    return render_template(

        "transactions.html",

        transactions=history

    )


# =========================================================
# PORTFOLIO ALLOCATION CHART
# =========================================================

@app.route("/allocation")
@login_required
def allocation():

    portfolio = get_portfolio(
        current_user.id
    )

    labels = []

    values = []

    for stock in portfolio.stocks.values():

        live_price = get_live_price(
            stock.name
        )

        value = (
            live_price *
            stock.quantity
        )

        labels.append(
            stock.name
        )

        values.append(
            round(
                value,
                2
            )
        )

    # Add cash
    if portfolio.balance > 0:

        labels.append("Cash")

        values.append(
            round(
                portfolio.balance,
                2
            )
        )

    return jsonify({

        "labels": labels,

        "values": values

    })


# =========================================================
# STOCK PRICE CHART
# =========================================================

@app.route(
    "/chart/<symbol>"
)
@login_required
def chart(symbol):

    symbol = symbol.upper()

    try:

        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="1mo"
        )

        dates = [

            date.strftime(
                "%Y-%m-%d"
            )

            for date in data.index

        ]

        prices = [

            round(
                float(price),
                2
            )

            for price
            in data["Close"]

        ]

        return jsonify({

            "dates": dates,

            "prices": prices

        })

    except:

        return jsonify({

            "dates": [],

            "prices": []

        })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )