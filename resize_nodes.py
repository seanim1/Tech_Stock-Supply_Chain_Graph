"""
resize_nodes.py
===============
Reads market cap from stock_dashboard.csv and updates the width
of company nodes in supply_chain.dot based on market cap tiers.

Usage:
    python3 resize_nodes.py
    python3 resize_nodes.py --dot supply_chain.dot --csv stock_dashboard.csv --out supply_chain.dot
"""

import re
import csv
import argparse

# ── Map ticker → dot node name ────────────────────────────────
TICKER_TO_NODE = {
    "META":      "s_META",
    "TSLA":      "s_TSLA",
    "AAPL":      "s_APPL",
    "AMZN":      "s_AMZN",
    "MSFT":      "s_MSFT",
    "GOOGL":     "s_GOOGL",
    "ANET":      "s_ANET",
    "CSCO":      "s_CSCO",
    "MU":        "s_MU",
    "SNDK":      "s_SNDK",
    "NVDA":      "s_NVDA",
    "AMD":       "s_AMD",
    "INTC":      "s_INTC",
    "ARM":       "s_ARM",
    "QCOM":      "s_QCOM",
    "STM":       "s_STM",
    "AVGO":      "s_AVGO",
    "005930.KS": "s_Samsung",
    "000660.KS": "s_SKHynix",
}

def parse_market_cap(val):
    """Convert '$1.61T' or '$200.80B' to float in billions."""
    if not val or val == "N/A":
        return None
    val = val.strip().lstrip("$")
    if val.endswith("T"):
        return float(val[:-1]) * 1000
    if val.endswith("B"):
        return float(val[:-1])
    return None

def cap_to_size(cap_b):
    """Map market cap in billions to (width, height) tuple."""
    if cap_b is None:   return (1.0, 1.0)
    if cap_b >= 4000:   return (5.0, 5.0)   # $4T+
    if cap_b >= 3000:   return (4.5, 4.5)   # $3T+
    if cap_b >= 2000:   return (4.0, 4.0)   # $2-3T
    if cap_b >= 1000:   return (3.5, 3.5)   # $1-2T
    if cap_b >= 500:    return (3.0, 3.0)   # $500B-1T
    if cap_b >= 200:    return (2.0, 2.0)   # $200-500B
    if cap_b >= 100:    return (1.5, 1.5)   # $100-200B
    return (1.0, 1.0)                        # <$100B

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dot", default="supply_chain.dot")
    parser.add_argument("--csv", default="stock_dashboard.csv")
    parser.add_argument("--out", default="supply_chain.dot")
    args = parser.parse_args()

    # ── Read market caps from CSV ─────────────────────────────
    caps = {}
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("Ticker", "").strip()
            node = TICKER_TO_NODE.get(ticker)
            if node:
                cap = parse_market_cap(row.get("Market Cap", ""))
                caps[node] = cap
                w, h = cap_to_size(cap)
                cap_str = f"${cap:.0f}B" if cap else "N/A"
                print(f"  {ticker:12} → {node:12}  cap={cap_str:10}  width={w}  height={h}")

    # ── Read dot file ─────────────────────────────────────────
    with open(args.dot, "r", encoding="utf-8") as f:
        dot = f.read()

    # ── Update width for each node ────────────────────────────
    for node, cap in caps.items():
        w, h = cap_to_size(cap)

        pattern = rf'(\b{re.escape(node)}\s*\[)([^\]]*?)(\])'

        def replacer(m, w=w, h=h):
            attrs = m.group(2)
            if re.search(r'\bwidth\s*=', attrs):
                attrs = re.sub(r'\bwidth\s*=\s*[\d.]+', f'width={w}', attrs)
            else:
                attrs = attrs.rstrip() + f', width={w}'
            if re.search(r'\bheight\s*=', attrs):
                attrs = re.sub(r'\bheight\s*=\s*[\d.]+', f'height={h}', attrs)
            else:
                attrs = attrs.rstrip() + f', height={h}'
            return m.group(1) + attrs + m.group(3)

        dot, n = re.subn(pattern, replacer, dot, flags=re.DOTALL)
        if n == 0:
            print(f"  Warning: node {node} not found in dot file")

    # ── Write output ──────────────────────────────────────────
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(dot)

    print(f"\n✓ Updated {args.out}")

if __name__ == "__main__":
    main()