from src.strategy_code_base.adhoc.backtester import logger
from src.strategy_code_base.client.angel_trading import create_connection
from src.strategy_code_base.utility.config import interval_data
import pandas as pd


def get_historical_data(obj, interval: str, from_date: str, to_date: str, symbol_token: str, exchange: str):
    try:
        historicParam = {
            "exchange": exchange,
            "symboltoken": symbol_token,
            "interval": interval,
            "fromdate": from_date,
            "todate": to_date
        }
        data = obj.getCandleData(historicParam)
        df = pd.DataFrame(data.get("data"), columns=["timestamp", "open", "high", "low", "close", "volume"])
        df.set_index(pd.DatetimeIndex(df["timestamp"]), inplace=True)
        return df
    except Exception as e:
        logger.error("Historic Api failed: {}".format(str(e)))


if __name__ == '__main__':
    obj = create_connection()
    interval_temp = interval_data.get(3)
    df = get_historical_data(obj, interval_temp, "2021-09-06 09:15", "2021-09-06 11:15", "BANKNIFTY", "NFO")
    from src.strategy_code_base.strategy.create_strategy import run_momentum_strategy
    print(run_momentum_strategy(df))
