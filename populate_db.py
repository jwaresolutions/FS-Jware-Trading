import sqlite3
import config as config
import alpaca_trade_api as tradeapi

connection = sqlite3.connect(config.db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

api = tradeapi.REST(
    config.key_id,
    config.secret_key,
    base_url=config.endpoint
)  # or use ENV Vars shown below
assets = api.list_assets()

cursor.execute("""
    SELECT symbol, company FROM stock
""")
rows = cursor.fetchall()
symbols = [row["symbol"] for row in rows]

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol} {asset.name}")
            cursor.execute("INSERT INTO stock (symbol, company) VALUES (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()
