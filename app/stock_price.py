# stock_price.py
# --------------
# Fetches live stock prices from Yahoo Finance.
# For Indian stocks, tickers need .NS (NSE) or .BO (BSE) suffix.

import yfinance as yf

# Common Indian stock name to ticker mappings
# So users can type "Infosys" instead of "INFY.NS"
STOCK_MAP = {
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "tcs": "TCS.NS",
    "tata consultancy": "TCS.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "reliance": "RELIANCE.NS",
    "ril": "RELIANCE.NS",
    "icici bank": "ICICIBANK.NS",
    "icicibank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",
    "wipro": "WIPRO.NS",
    "hcl": "HCLTECH.NS",
    "hcl tech": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "axis bank": "AXISBANK.NS",
    "axisbank": "AXISBANK.NS",
    "axis": "AXISBANK.NS",
    "kotak": "KOTAKBANK.NS",
    "kotak bank": "KOTAKBANK.NS",
    "kotakbank": "KOTAKBANK.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "bajfinance": "BAJFINANCE.NS",
    "sbi": "SBIN.NS",
    "state bank": "SBIN.NS",
    "maruti": "MARUTI.NS",
    "maruti suzuki": "MARUTI.NS",
    "sun pharma": "SUNPHARMA.NS",
    "sunpharma": "SUNPHARMA.NS",
    "dr reddy": "DRREDDY.NS",
    "dr reddys": "DRREDDY.NS",
    "drreddy": "DRREDDY.NS",
    "cipla": "CIPLA.NS",
    "asian paints": "ASIANPAINT.NS",
    "asianpaint": "ASIANPAINT.NS",
    "titan": "TITAN.NS",
    "nestle": "NESTLEIND.NS",
    "itc": "ITC.NS",
    "larsen": "LT.NS",
    "l&t": "LT.NS",
    "lt": "LT.NS",
    "ultratech": "ULTRACEMCO.NS",
    "ultratech cement": "ULTRACEMCO.NS",
    "ntpc": "NTPC.NS",
    "ongc": "ONGC.NS",
    "powergrid": "POWERGRID.NS",
    "power grid": "POWERGRID.NS",
    "tata motors": "TATAMOTORS.NS",
    "tatamotors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS",
    "tatasteel": "TATASTEEL.NS",
    "jsw steel": "JSWSTEEL.NS",
    "jswsteel": "JSWSTEEL.NS",
    "hindalco": "HINDALCO.NS",
    "bajaj auto": "BAJAJ-AUTO.NS",
    "hero motocorp": "HEROMOTOCO.NS",
    "heromotoco": "HEROMOTOCO.NS",
    "tech mahindra": "TECHM.NS",
    "techm": "TECHM.NS",
    "adani ports": "ADANIPORTS.NS",
    "adaniports": "ADANIPORTS.NS",
    "adani enterprises": "ADANIENT.NS",
    "britannia": "BRITANNIA.NS",
    "divis lab": "DIVISLAB.NS",
    "divislab": "DIVISLAB.NS",
    "eicher motors": "EICHERMOT.NS",
    "eichermot": "EICHERMOT.NS",
    "grasim": "GRASIM.NS",
    "indusind bank": "INDUSINDBK.NS",
    "indusindbk": "INDUSINDBK.NS",
    "m&m": "M&M.NS",
    "mahindra": "M&M.NS",
    "shree cement": "SHREECEM.NS",
    "shreecem": "SHREECEM.NS",
    "tata consumer": "TATACONSUM.NS",
    "upl": "UPL.NS",
    "vedanta": "VEDL.NS",
    "zomato": "ZOMATO.NS",
    "paytm": "PAYTM.NS",
    "nykaa": "NYKAA.NS",
    "policybazaar": "POLICYBZR.NS",
}


def get_ticker(stock_name: str) -> str:
    """
    Convert a stock name to its Yahoo Finance ticker.
    e.g. "Infosys" -> "INFY.NS"
    If not found in map, assumes it's already a ticker and adds .NS if needed.
    """
    name_lower = stock_name.strip().lower()

    # Check our mapping first
    if name_lower in STOCK_MAP:
        return STOCK_MAP[name_lower]

    # If it already looks like a ticker with suffix, use as is
    if "." in stock_name:
        return stock_name.upper()

    # Otherwise add .NS and try
    return stock_name.upper() + ".NS"


def get_live_price(stock_name: str) -> dict:
    """
    Fetch the current live price for a stock.

    Returns a dict:
    {
        "success": True/False,
        "price": 1234.56,
        "ticker": "INFY.NS",
        "name": "Infosys Limited",
        "currency": "INR",
        "error": "error message if failed"
    }
    """
    ticker_symbol = get_ticker(stock_name)

    try:
        ticker = yf.Ticker(ticker_symbol)
        info   = ticker.info

        # Try to get current price from different fields
        price = (
            info.get("currentPrice") or
            info.get("regularMarketPrice") or
            info.get("previousClose")
        )

        if not price or price <= 0:
            # Try fast_info as backup
            fast = ticker.fast_info
            price = getattr(fast, "last_price", None)

        if not price or price <= 0:
            return {
                "success": False,
                "ticker": ticker_symbol,
                "error": f"Could not fetch price for {ticker_symbol}. Please enter price manually."
            }

        return {
            "success":  True,
            "price":    round(float(price), 2),
            "ticker":   ticker_symbol,
            "name":     info.get("longName") or info.get("shortName") or stock_name,
            "currency": info.get("currency", "INR"),
        }

    except Exception as e:
        return {
            "success": False,
            "ticker":  ticker_symbol,
            "error":   f"Error fetching price: {str(e)}. Please enter price manually."
        }
