import strategies.Orders as order
import argparse

parser = argparse.ArgumentParser(description='Execute trades programmatically')

parser.add_argument('--symbol', dest='symbol', type=str, help='Symbol you want to trade')
parser.add_argument('--direction', dest='Direction', type=str, help='buy or sell')

args = parser.parse_args()
symbol = args.symbol


max_spend = order.process_limits('AAPL')
order.fractional_order(str(symbol), max_spend)