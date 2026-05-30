"""
AI Supply Chain Stock Dashboard
================================
Pulls revenue, net income, net margin (last 2 quarters),
market cap, and price change (1M, 3M, 6M, 1Y).
Korean stocks are converted from KRW to USD.

Requirements:
    pip install yfinance pandas tabulate

Run:
    python us_analysis.py
"""

import yfinance as yf
import pandas as pd
from tabulate import tabulate
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

STOCKS = {
    # US stocks
    "META":      ("Meta 메타",            "Software"),
    "TSLA":      ("Tesla 테슬라",           "Hardware"),
    "AAPL":      ("Apple 애플",           "Hardware"),
    "AMZN":      ("Amazon 아마존",          "Cloud"),
    "MSFT":      ("Microsoft 마이크로소프트",       "Cloud"),
    "GOOGL":     ("Alphabet 알파벳",        "Cloud"),
    "ANET":      ("Arista 아리스타",          "Network"),
    "CSCO":      ("Cisco 시스코",           "Network"),
    "MU":        ("Micron 마이크론",          "Memory"),
    "SNDK":      ("SanDisk 샌디스크",         "Memory"),
    "NVDA":      ("NVIDIA 엔비디아",          "Compute"),
    "AMD":       ("AMD",             "Compute"),
    "INTC":      ("Intel 인텔",           "Compute"),
    "ARM":       ("Arm Holdings 암홀딩스",    "Compute"),
    "QCOM":      ("Qualcomm 퀄컴",        "Compute"),
    "STM":       ("STMicro",         "Compute"),
    "AVGO":      ("Broadcom 브로드컴",        "Compute"),
    # Korean stocks
    "005930.KS": ("Samsung 삼성전자",         "Memory"),
    "000660.KS": ("SK Hynix 하이닉스",        "Memory"),
}

def get_krw_to_usd():
    """Fetch live KRW/USD rate via Yahoo Finance (KRWUSD=X)."""
    try:
        rate = yf.Ticker("KRWUSD=X").history(period="1d")["Close"].iloc[-1]
        print(f"   KRW/USD rate: {rate:.6f} (1 KRW = ${rate:.6f})")
        return float(rate)
    except Exception:
        fallback = 0.00073  # approximate fallback
        print(f"   Warning: could not fetch KRW/USD, using fallback {fallback}")
        return fallback

def fmt_billions(val):
    if val is None or pd.isna(val):
        return "N/A"
    b = val / 1e9
    if b >= 1000:
        return f"${b/1000:.2f}T"
    return f"${b:.2f}B"

def fmt_pct(val):
    if val is None or pd.isna(val):
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"

def fmt_margin(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.1f}%"

def get_price_changes(ticker_obj):
    try:
        today = datetime.today()
        hist = ticker_obj.history(period="13mo")
        if hist.empty:
            return None, None, None, None
        current = hist["Close"].iloc[-1]
        def delta(days):
            cutoff = today - timedelta(days=days)
            past = hist["Close"][hist.index <= cutoff.strftime("%Y-%m-%d")]
            if past.empty:
                return None
            return (current - past.iloc[-1]) / past.iloc[-1] * 100
        return delta(30), delta(90), delta(180), delta(365)
    except Exception:
        return None, None, None, None

def get_market_cap(ticker_obj):
    try:
        mc = ticker_obj.info.get("marketCap")
        return float(mc) if mc else None
    except Exception:
        return None

def get_financials(symbol, krw_rate=1.0):
    try:
        t = yf.Ticker(symbol)
        income = t.quarterly_income_stmt
        if income is None or income.empty:
            return None

        cols = income.columns[:2]
        is_korean = symbol.endswith(".KS")

        def get_val(row_names, col):
            for name in row_names:
                if name in income.index:
                    val = income.loc[name, col]
                    if not pd.isna(val):
                        v = float(val)
                        return v * krw_rate if is_korean else v
            return None

        results = []
        for col in cols:
            rev = get_val(["Total Revenue", "Revenue"], col)
            ni  = get_val(["Net Income", "Net Income Common Stockholders"], col)
            margin = (ni / rev * 100) if rev and ni and rev != 0 else None
            quarter_label = col.strftime("Q ending %b %Y") if hasattr(col, 'strftime') else str(col)
            results.append({"quarter": quarter_label, "revenue": rev, "net_income": ni, "margin": margin})

        c1m, c3m, c6m, c1y = get_price_changes(t)
        market_cap = get_market_cap(t)
        if is_korean and market_cap:
            market_cap *= krw_rate

        return {
            "q1": results[0] if len(results) > 0 else {},
            "q2": results[1] if len(results) > 1 else {},
            "change_1m": c1m, "change_3m": c3m,
            "change_6m": c6m, "change_1y": c1y,
            "market_cap": market_cap,
        }
    except Exception as e:
        print(f"  Warning: could not fetch {symbol} — {e}")
        return None

def main():
    print("\n📊 AI Supply Chain Stock Dashboard")
    print(f"   Fetched: {datetime.today().strftime('%Y-%m-%d %H:%M')}\n")

    krw_rate = get_krw_to_usd()
    print(f"   Fetching data for {len(STOCKS)} stocks...\n")

    rows = []
    for symbol, (name, group) in STOCKS.items():
        print(f"   Pulling {symbol}...", end="\r")
        data = get_financials(symbol, krw_rate)

        if data:
            q1 = data.get("q1", {})
            q2 = data.get("q2", {})
            rows.append({
                "Ticker":     symbol,
                "Name":       name,
                "Group":      group,
                "Market Cap": fmt_billions(data.get("market_cap")),
                "Rev Q1":     fmt_billions(q1.get("revenue")),
                "Net Inc Q1": fmt_billions(q1.get("net_income")),
                "Margin Q1":  fmt_margin(q1.get("margin")),
                "Rev Q2":     fmt_billions(q2.get("revenue")),
                "Net Inc Q2": fmt_billions(q2.get("net_income")),
                "Margin Q2":  fmt_margin(q2.get("margin")),
                "Δ 1 Month":  fmt_pct(data.get("change_1m")),
                "Δ 3 Month":  fmt_pct(data.get("change_3m")),
                "Δ 6 Month":  fmt_pct(data.get("change_6m")),
                "Δ 1 Year":   fmt_pct(data.get("change_1y")),
                "Q1 Period":  q1.get("quarter", "N/A"),
            })
        else:
            rows.append({
                "Ticker": symbol, "Name": name, "Group": group,
                "Market Cap": "N/A",
                "Rev Q1": "N/A", "Net Inc Q1": "N/A", "Margin Q1": "N/A",
                "Rev Q2": "N/A", "Net Inc Q2": "N/A", "Margin Q2": "N/A",
                "Δ 1 Month": "N/A", "Δ 3 Month": "N/A",
                "Δ 6 Month": "N/A", "Δ 1 Year": "N/A",
                "Q1 Period": "N/A",
            })

    df = pd.DataFrame(rows)

    display_cols = [
        "Ticker", "Name", "Market Cap",
        "Rev Q1", "Net Inc Q1", "Margin Q1",
        "Rev Q2", "Net Inc Q2", "Margin Q2",
        "Δ 1 Month", "Δ 3 Month", "Δ 6 Month", "Δ 1 Year",
    ]

    for group in ["Memory", "Compute", "Cloud", "Network", "Software", "Hardware", "ETF"]:
        subset = df[df["Group"] == group][display_cols]
        if subset.empty:
            continue
        print(f"\n── {group} {'─' * (50 - len(group))}")
        print(tabulate(subset, headers="keys", tablefmt="simple", showindex=False))

    print("\n── Notes ───────────────────────────────────────────────")
    print("   Q1 = most recent quarter, Q2 = prior quarter")
    print("   All values in USD — Korean stocks converted at live KRW/USD rate")
    print("   Net Margin = Net Income / Revenue × 100")
    print("   Price deltas are in local currency % terms (KRW for Korean stocks)")
    print("   VOO shown as S&P 500 benchmark — no revenue/earnings data")
    print("   SNDK (SanDisk) recently spun off — data may be limited")
    print("   Source: Yahoo Finance via yfinance\n")

    csv_path = "stock_dashboard.csv"
    df.to_csv(csv_path, index=False)
    print(f"   ✓ Full data saved to {csv_path}\n")

if __name__ == "__main__":
    main()