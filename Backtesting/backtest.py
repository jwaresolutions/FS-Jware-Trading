import alpaca_connection
import backtrader, pandas, sqlite3
from datetime import date, datetime, time, timedelta

alpaca_connect = alpaca_connection.Alpaca_Connect()


class OpeningRangeBreakout(backtrader.Strategy):
    params = dict(
        num_opening_bars=15
    )

    def __init__(self):
        self.opening_range_low = 0
        self.opening_range_high = 0
        self.opening_range = 0
        self.bought_today = False
        self.order = None
        self.direction = 'None'

    def log(self, txt, dt=None):
        if dt is None:
            dt = self.datas[0].datetime.datetime()

        print('%s, %s' % (dt, txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            order_details = f"{order.executed.price}, Cost: {order.executed.value}, Comm {order.executed.comm}"

            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order_details}")
            else:  # Sell
                self.log(f"SELL EXECUTED, Price: {order_details}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        current_bar_datetime = self.data.num2date(self.data.datetime[0])
        previous_bar_datetime = self.data.num2date(self.data.datetime[-1])

        if current_bar_datetime.date() != previous_bar_datetime.date():
            self.opening_range_low = self.data.low[0]
            self.opening_range_high = self.data.high[0]
            self.bought_today = False
            self.direction = 'None'

        opening_range_start_time = time(9, 30, 0)
        dt = datetime.combine(date.today(), opening_range_start_time) + timedelta(minutes=self.p.num_opening_bars)
        opening_range_end_time = dt.time()

        if current_bar_datetime.time() >= opening_range_start_time \
                and current_bar_datetime.time() < opening_range_end_time:
            self.opening_range_high = max(self.data.high[0], self.opening_range_high)
            self.opening_range_low = min(self.data.low[0], self.opening_range_low)
            self.opening_range = self.opening_range_high - self.opening_range_low
        else:
            if self.order:
                return

            if self.position and (self.data.close[0] > (
                    self.opening_range_high + self.opening_range) and self.direction == 'Breakout'):
                self.close()

            if self.position and (self.data.close[0] < (
                    self.opening_range_low - self.opening_range) and self.direction == 'Breakdown'):
                self.close()

            if self.data.close[
                0] > self.opening_range_high and not self.position and not self.bought_today and self.data.close[0] > \
                    self.data.sma_20[0] and self.data.close[0] > self.data.sma_50[0]:
                self.order = self.buy()
                self.bought_today = True
                self.direction = "Breakout"

            if self.data.close[
                0] < self.opening_range_low and not self.position and not self.bought_today and self.data.close[0] < \
                    self.data.sma_20[0] and self.data.close[0] < self.data.sma_50[0]:
                self.order = self.sell()
                self.bought_today = True
                self.direction = "Breakdown"

            if self.position and (self.data.close[0] < (
                    self.opening_range_high - self.opening_range) and self.direction == 'Breakout'):
                self.order = self.close()

            if self.position and (self.data.close[0] > (
                    self.opening_range_low + self.opening_range) and self.direction == 'Breakdown'):
                self.order = self.close()

            if self.position and current_bar_datetime.time() >= time(15, 45, 0):
                self.log("RUNNING OUT OF TIME - LIQUIDATING POSITION")
                self.close()

    def stop(self):
        self.log('(Num Opening Bars %2d) Ending Value %.2f' %
                 (self.params.num_opening_bars, self.broker.getvalue()))

        if self.broker.getvalue() > 130000:
            self.log(f"*** {self.current_symbol} BIG WINNER ***")

        elif self.broker.getvalue() < 70000:
            self.log(f"*** {self.current_symbol} MAJOR LOSER ***")

        else:
            self.log(f"*** {self.current_symbol} INEFFECTIVE ***")


if __name__ == '__main__':
    conn = sqlite3.connect(alpaca_connect.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT(stock_id) as stock_id FROM stock_price_minute
    """)
    stocks = cursor.fetchall()

    stocks = [stocks[0]]

    for stock in stocks:
        print(f"== Testing {stock['stock_id']} ==")

        cerebro = backtrader.Cerebro()
        cerebro.broker.setcash(100000.0)
        cerebro.addsizer(backtrader.sizers.PercentSizer, percents=95)

        dataframe = pandas.read_sql("""
            select datetime, open, high, low, close, volume, sma_20, sma_50, rsi_14
            from stock_price_minute
            where stock_id = :stock_id
            and strftime('%H:%M:%S', datetime) >= '09:30:00' 
            and strftime('%H:%M:%S', datetime) < '16:00:00'
            order by datetime asc
        """, conn, params={"stock_id": stock['stock_id']}, index_col='datetime', parse_dates=['datetime'])

        data = backtrader.feeds.PandasData(dataname=dataframe)

        cerebro.adddata(data)
        cerebro.addstrategy(OpeningRangeBreakout)

        # strats = cerebro.optstrategy(OpeningRangeBreakout, num_opening_bars=[15, 30, 60])

        cerebro.run()
        # cerebro.plot()
