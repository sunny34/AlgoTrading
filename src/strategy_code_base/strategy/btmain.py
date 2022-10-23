import datetime
import backtrader as bt
from strategies import *
import pandas as pd
cerebro = bt.Cerebro()

# Add a strategy
cerebro.addstrategy(TestStrategy)

# Datas are in a subfolder of the samples. Need to find where the script is
# because it could have been called from anywhere
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = "/home/sunny/Downloads/Telegram Desktop/2018-08-30.csv"

df = pd.read_csv(filepath_or_buffer=datapath)
df["0"] = pd.to_datetime(df["0"]).dt.strftime('%Y-%m-%d %H:%M:%S')

df.to_csv("mod_file.csv", index=False)
# Create a Data Feed
data = bt.feeds.GenericCSVData(
    dataname="mod_file.csv",
    # Do not pass values before this date
    # fromdate=datetime.datetime(2000, 1, 1),
    # Do not pass values before this date
    # todate=datetime.datetime(2000, 12, 31),
    # Do not pass values after this date
    reverse=False)

# Add the Data Feed to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(100000.0)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything
# cerebro.run()
#
# # Print out the final result
# print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

if __name__ == '__main__':
    optimized_runs = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # final_results_list = []
    # for run in optimized_runs:
    #     for strategy in run:
    #         PnL = round(strategy.broker.get_value() - 10000, 2)
    #         sharpe = strategy.analyzers.sharpe_ratio.get_analysis()
    #         final_results_list.append([strategy.params.pfast,
    #                                    strategy.params.pslow, PnL, sharpe['sharperatio']])
    #
    # sort_by_sharpe = sorted(final_results_list, key=lambda x: x[3],
    #                         reverse=True)
    # for line in sort_by_sharpe[:5]:
    #     print(line)
