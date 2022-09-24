import pandas as pd
from numba import jit
import numpy as np
import pandas_ta as ta


def run_momentum_strategy(df):
    result = df.ta.strategy("Momentum")
    return result

@jit
def np_vwap(volume: int, high: int, low: int):
    """
    Function to calculate the vwap and enhances performance by using jit

    :param volume: volume of the candle
    :param high: high of the candle
    :param low: low of the candle
    :return:
    """
    return np.cumsum(volume*(high+low)/2) / np.cumsum(volume)


def create_direction_strategy(df):
    volume = df.volume.values
    high = df.high.values
    low = df.low.values
    df['vwap'] = np_vwap(volume, high, low)
