import yfinance as yf

def get_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")

    if data.empty:
        return None

    return round(data["Close"].iloc[-1], 2)