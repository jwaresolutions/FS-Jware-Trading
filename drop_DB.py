import sqlite3
import config as config
connection = sqlite3.connect(config.db_path)

cursor = connection.cursor()

cursor.execute("""
    DROP TABLE stock_price
""")

cursor.execute("""
    DROP TABLE stock
""")

connection.commit()
