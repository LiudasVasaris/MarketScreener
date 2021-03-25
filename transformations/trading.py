# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 19:48:38 2020

@author: juliu
"""
import datetime
from typing import Dict, Any, Callable

import pandas as pd
import yfinance as yf
from pandas import DataFrame
from ta.volatility import BollingerBands

from utilities.screener_logger import logger

pd.options.mode.chained_assignment = None  # default='warn'


class Stock:
    """
    name: stock indicator name such as AAPL
    interval: interval of stock data calculations
    period: period for which to return data from
    """

    def __init__(self, name, interval="1d", period=None):
        self.name = name
        self.interval = interval
        self.ticker = yf.Ticker(name)
        self.fullname = self.ticker.info["shortName"]
        self.data = self.update_data(period)

    def update_data(self, period):

        self.ticker = yf.Ticker(self.name)
        if "60m" in self.interval:
            period_ = "2y"
        elif "m" in self.interval:
            period_ = "60d"
        else:
            period_ = "max"

        period_ = period or period_
        data_ny_tz = self.ticker.history(interval=self.interval, period=period_)
        try:
            data_lt_tz = localize_time(data_ny_tz)
        except TypeError:
            data_lt_tz = data_ny_tz
        return data_lt_tz

    def get_current_price(self):
        current_price = self.ticker.history(interval="1m", period="1d").iloc[-1]
        return current_price


def return_on_hold(
    data: pd.DataFrame, price: str = "Close", period: int = 365
) -> Dict[Any, Any]:
    """Returns Dict of returns in for holding period of time
    :param data: dataframe containing stock info
    :param price: for which price returns are calculated
    :param period: days of holding stock

    :return: Dict of returns of holding around period of time
    """
    df = data
    delta = df.index.max() - df.index.min()

    if delta.days < period:
        logger.info("Contains less days than period, setting period to maximum")
        period=delta.days

    return_dict = {}

    for i in df.index:
        price_cur = df[price][i]
        year_time = i + datetime.timedelta(days=period)
        try:
            closest_approx = max(filter(lambda x: x <= year_time, df.index))
            price_year = df[price][closest_approx]
            return_dict[i] = price_year / price_cur
        except:
            pass

    return return_dict


def return_on_strategy(
    data: DataFrame,
    price: str = "Close",
    strategy_indicator: str = "bb_bbli",
    period=365,
) -> Dict[Any, Any]:
    df = data
    delta = df.index.max() - df.index.min()

    if delta.days < period:
        logger.info("Contains less days than period, setting period to maximum")
        period=delta.days

    return_dict = {}

    for i in df[df[strategy_indicator] == 1].index:
        price_cur = df[price][i]
        year_time = i + datetime.timedelta(days=period)
        try:
            closest_aprox = max(filter(lambda x: x <= year_time, df.index))
            price_year = df[price][closest_aprox]
            return_dict[i] = price_year / price_cur
        except:
            pass

    return return_dict


def bollinger_bands(
    data: DataFrame, days: int = 20, std: int = 2, price="Close"
) -> DataFrame:
    df = data
    # Initialize Bollinger Bands Indicator
    indicator_bb = BollingerBands(close=df[price], window=days, window_dev=std)
    # Add Bollinger Bands features
    df["bb_ma"] = indicator_bb.bollinger_mavg()
    df["bb_high"] = indicator_bb.bollinger_hband()
    df["bb_low"] = indicator_bb.bollinger_lband()

    # Add Bollinger Band high indicator
    df["bb_bbhi"] = indicator_bb.bollinger_hband_indicator()

    # Add Bollinger Band low indicator
    df["bb_bbli"] = indicator_bb.bollinger_lband_indicator()

    return df


def localize_time(data):
    data["date_lt"] = data.index.tz_convert("Europe/Vilnius")
    data_local = data.set_index("date_lt")
    return data_local


def buy_signal_filter(
    stock: Stock, strategy: Callable, strategy_indicator: str, check_periods: int = 3
):
    df = strategy(stock.data)
    if sum(df[strategy_indicator].iloc[check_periods * -1 :]) != 0:
        return True
    return False
