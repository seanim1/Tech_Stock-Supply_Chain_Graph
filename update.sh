python3 -m venv venv
source venv/bin/activate
pip install yfinance pandas tabulate
python3 analyze.py
python3 resize_nodes.py
python3 resize_nodes.py --dot supply_chain.dot --csv stock_dashboard.csv --out supply_chain.dot
