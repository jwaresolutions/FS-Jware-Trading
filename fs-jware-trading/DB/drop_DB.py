import sqlite3
from API import alpaca_connection as ac

alpaca_connect = ac.Alpaca_Connect()

connection = sqlite3.connect(f"../{alpaca_connect.db_path}")

cursor = connection.cursor()

cursor.execute("""
    DROP TABLE stock_price
""")

cursor.execute("""
    DROP TABLE stock
""")

cursor.execute("""
    DROP TABLE strategy
""")

connection.commit()
