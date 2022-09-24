import datetime
import time

from nsepy import get_history
import pandas as pd
from src.strategy_code_base import logger
from dateutil.relativedelta import relativedelta
from create_date_required import create_final_result
import holidays

logger.add("file_{time}.log", format="{name}{message}", level="DEBUG")


def get_data():
    """
    Read NSE 100 data

    :return: dataframe of the nifty 100
    """
    df = pd.read_csv('https://www1.nseindia.com/content/indices/ind_nifty100list.csv')
    return df


def get_change(current, previous):
    """
    Function which calculates percent change

    :param current: current price
    :param previous: historical price
    :return: percent return
    """
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0


def check_holiday(user_date):
    """
    Function whether date is Indian holiday

    :param user_date: date
    :return: modified date
    """
    indian_holidays = holidays.IN()
    if user_date in indian_holidays:
        logger.info(f"current date {user_date} is Indian Holiday going to next date")
        user_date = user_date + relativedelta(days=1)
    return user_date


def get_next_valid_date(user_date):
    """
    Function which checks if date is either weekend i.e. saturday or sunday and make required adjustment

    :param user_date: date
    :return: modified date
    """
    if user_date.weekday() == 5:
        logger.info("day is Saturday adding 2 more days")
        user_date = user_date + relativedelta(days=2)
    if user_date.weekday() == 6:
        logger.info("day is Sunday adding 1 more days")
        user_date = user_date + relativedelta(days=2)
    user_date = check_holiday(user_date)
    return user_date


def get_historical_data_per_month(df):
    """
    function which creates required dates and call
    :param df:
    :return:
    """
    final_result = list()
    start_date = datetime.datetime(2022, 5, 1)
    end_date = datetime.datetime.now()
    total_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
    for x in range(0, total_months):
        starting_date = start_date + relativedelta(months=x)
        starting_date = get_next_valid_date(starting_date)
        date_relative = starting_date - relativedelta(months=6)
        date_relative = get_next_valid_date(date_relative)
        temp_df = create_historical_data(df, starting_date, date_relative)
        if not temp_df.empty:
            final_result.append(temp_df)
    if final_result:
        logger.info("Creating final data frame")
        final_df = pd.concat(final_result, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()


def create_historical_data(df, starting_date, date_relative):
    temp_result = list()
    for index, row in df.iterrows():
        symbol = row['Symbol']
        logger.opt(colors=True).info(f"starting getting data for <blue>{symbol}</blue>"
                                     f" <yellow>current date {starting_date}</yellow> "
                                     f"<blue>historical date {date_relative}</blue>")
        current_data = get_history(symbol=symbol, start=starting_date,
                                   end=starting_date)
        current_data_new = current_data[['Symbol', 'Close']]
        current_data_new = current_data_new.assign(execution_date=starting_date)
        current_data_new.rename(columns={"Close": "current_price"}, inplace=True)
        historical_data = get_history(symbol=symbol, start=date_relative,
                                      end=date_relative)
        historical_data_new = historical_data[['Symbol', 'Close']]
        historical_data_new = historical_data_new.assign(historical_date=date_relative)
        historical_data_new.rename(columns={"Close": "historical_price"}, inplace=True)
        if historical_data_new.empty:
            logger.opt(colors=True).warning(f"historical data missing for symbol <blue>{symbol}</blue> date "
                                            f"<red>{date_relative}</red>")
        if current_data_new.empty:
            logger.opt(colors=True).warning(f"current data missing for symbol <blue>{symbol}</blue> date <red>{starting_date}</red>")
        final_data = pd.merge(current_data_new, historical_data_new, on="Symbol")
        if not final_data.empty:
            final_data['percent_change'] = final_data.apply(lambda row: get_change(row["current_price"],
                                                                                   row["historical_price"]), axis=1)
            temp_result.append(final_data)
        else:
            pass
        time.sleep(1)
    if temp_result:
        temp_df = pd.concat(temp_result, ignore_index=True)
        df1 = temp_df.sort_values('percent_change', ascending=False).groupby(
            ['execution_date', 'historical_date']).head(20)
        return df1
    else:
        df_temp = pd.DataFrame()
        return df_temp


def main():
    df = get_data()
    data = get_historical_data_per_month(df)
    result = create_final_result(data)
    result.to_csv("trending_stocks.csv", index=False)


if __name__ == '__main__':
    main()
