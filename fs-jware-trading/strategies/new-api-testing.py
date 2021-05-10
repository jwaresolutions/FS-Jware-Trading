import sqlite3
from API.alpaca_connection import Alpaca_Connect
import helpers as helpers
from strategies.Orders import order, send_message

ac = Alpaca_Connect()

ac.api.