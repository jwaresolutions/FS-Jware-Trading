import smtplib
import sqlite3
import ssl
from datetime import date
import alpaca_trade_api as tradeapi
import alpaca_connection


class OpeningRangeBreakOutDownClass:
    def __init__(self):
        self.alpaca_connect = alpaca_connection.Alpaca_Connect()
        self.context = ssl.create_default_context()
        self.messages = []
        self.current_date = date.today().isoformat()
        self.API_KEY = 'emptykey'
        self.API_KEY = self.alpaca_connect.key_id
        self.SECRET_KEY = self.alpaca_connect.secret_key
        self.API_URL = self.alpaca_connect.endpoint
        self.db_path = self.alpaca_connect.db_path
        self.new_order = False
        self.strategy_type = ''
        self.dst_check()
        self.strategy_check()

        if self.new_order:
            self.notification()

    def strategy_check(self):
        self.strategy_type = 'opening_range_breakout'
        self.side = 'buy'
        self.strategy()
        strategy_type = 'opening_range_breakdown'
        self.side = 'sell'
        self.strategy()
        self.notification()

    def dst_check(self):
        if is_dst():
            print("daylight savings")
            self.start_minute_bar = f"{self.current_date} 09:30:00-04:00"
            self.end_minute_bar = f"{self.current_date} 09:45:00-04:00"
        else:
            print("not daylight savings")
        self.start_minute_bar = f"{self.current_date} 09:30:00-05:00"
        self.end_minute_bar = f"{self.current_date} 09:45:00-05:00"

    def notification(self):
        print(self.messages)
        if self.new_order:
            self.new_order = False
            with smtplib.SMTP_SSL(self.alpaca_connect.email_host, self.alpaca_connect.email_port,
                                  context=self.context) as server:
                server.login(self.alpaca_connect.email_address, self.alpaca_connect.email_password)
                email_message = f"Subject: Trade Notification for {self.current_date}\n\n"
                email_message += "\n\n".join(self.messages)
                server.sendmail(self.alpaca_connect.email_address, self.alpaca_connect.email_address, email_message)
                server.sendmail(self.alpaca_connect.email_address, self.alpaca_connect.email_sms, email_message)

    def order(self, limit_price, profit_at, stop_loss_at):
        api = tradeapi.REST(self.API_KEY, self.SECRET_KEY, base_url=self.API_URL)
        api.submit_order(
            symbol=self.symbol,
            side=self.side,
            type='limit',
            qty='1',
            time_in_force='day',
            order_class='bracket',
            limit_price=limit_price,
            take_profit=profit_at,
            stop_loss=stop_loss_at
        )

    def strategy(self):
        api = tradeapi.REST(self.API_KEY, self.SECRET_KEY, base_url=self.API_URL)
        orders = api.list_orders(status='all', after=f"{self.current_date}T13:30:00Z")
        existing_order_symbols = [order.symbol for order in orders if order != 'canceled']
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("""
            select id from strategy where name = (?)
        """, (self.strategy_type,))

        strategy_id = cursor.fetchone()['id']

        cursor.execute("""
            select symbol, name
            from stock
            join stock_strategy on stock_strategy.stock_id = stock.id
            where stock_strategy.strategy_id = ?
        """, (strategy_id,))

        stocks = cursor.fetchall()
        symbols = [stock['symbol'] for stock in stocks]

        for symbol in symbols:
            minute_bars = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=self.current_date,
                                                      to=self.current_date).df
            print(f"{symbol} and {self.strategy_type}")
            # create a mask to only show the first 15 min of price data after the markets open
            opening_range_mask = (minute_bars.index >= self.start_minute_bar) & (
                    minute_bars.index < self.end_minute_bar)
            # resulting data from the mask
            opening_range_bars = minute_bars.loc[opening_range_mask]
            print(opening_range_bars)
            # find the lowest value in that 15 min period
            opening_range_low = opening_range_bars['low'].min()
            # find the highest value in that 15 min period
            opening_range_high = opening_range_bars['low'].max()
            # calculate the difference between the low and high for that 15 min period
            opening_range = opening_range_high - opening_range_low
            # mask data only include stock data after opening 15 min period
            after_opening_range_mask = minute_bars.index <= self.end_minute_bar
            after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
            after_opening_range_breakout = after_opening_range_bars[
                after_opening_range_bars['close'] > opening_range_high]
            after_opening_range_breakdown = after_opening_range_bars[
                after_opening_range_bars['close'] < opening_range_low]

            if self.strategy_type == 'breakout':
                if not after_opening_range_breakout.empty and symbol not in existing_order_symbols:
                    self.new_order = True
                    limit_price = after_opening_range_breakout.iloc[0]['close']
                    self.messages.append(
                        f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
                    print(
                        f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
                    profit_at = dict(limit_price=limit_price + opening_range, )
                    stop_loss_at = dict(limit_price=limit_price - opening_range, )
                    self.order(limit_price, profit_at, stop_loss_at)
                elif after_opening_range_breakdown.empty and symbol not in existing_order_symbols:
                    self.new_order = True
                    limit_price = after_opening_range_breakdown.iloc[0]['close']
                    self.messages.append(
                        f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
                    print(
                        f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
                    profit_at = dict(limit_price=limit_price - opening_range, )
                    stop_loss_at = dict(limit_price=limit_price + opening_range, )
                    self.order(limit_price, profit_at, stop_loss_at)
                else:
                    print(f'Order for {symbol} already exists, current list of orders {existing_order_symbols}')


run = OpeningRangeBreakOutDownClass
