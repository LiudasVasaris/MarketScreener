# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 19:48:38 2020

@author: juliu
"""
import datetime
import re
from pathlib import Path
from time import sleep

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from plotly.offline import plot
from ta.volatility import BollingerBands

from utilities.screener_logger import logger

pd.options.mode.chained_assignment = None  # default='warn'


def return_on_hold(data: pd.DataFrame, price: str = "Close", period: int = 365):
    df = data
    delta = df.index.max() - df.index.min()

    if delta.days < period:
        raise ValueError("Contains less days than period")

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


def return_on_strategy(data, price="Close", strategy_indicator="bb_bbli", period=365):
    df = data
    delta = df.index.max() - df.index.min()

    if delta.days < period:
        raise ValueError("Contains less days than period")

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


def bollinger_bands(data, days=20, std=2, price="Close"):
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


class Stock:
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
        current_price = self.ticker.history(interval='1m', period='1d').iloc[-1]
        return current_price



def plot_compare_stocks(
    stocks=None, strategy=bollinger_bands, date_from=None, date_to=None, period=365
):
    if stocks is None:
        stocks = []
    list_of_comparisons = []

    for stock in stocks:
        logger.info(f"adding {stock.fullname} to comparison")
        data = stock.data
        strategy_data = strategy(data)

        if date_from:
            strategy_data = strategy_data[date_from:]
            data = data[date_from:]
        if date_to:
            strategy_data = strategy_data[:date_to]
            data = data[:date_to]

        dict_hold = return_on_hold(data, period=period)
        dict_str = return_on_strategy(strategy_data, period=period)

        df_hold = pd.DataFrame(dict_hold.items(), columns=["Date", "Hold"]).set_index(
            "Date"
        )
        df_STR = pd.DataFrame(dict_str.items(), columns=["Date", "Strategy"]).set_index(
            "Date"
        )

        df_merged = df_hold.merge(df_STR, left_index=True, right_index=True, how="left")

        df_fin = pd.melt(
            df_merged.reset_index(),
            id_vars=["Date"],
            value_vars=["Hold", "Strategy"],
            value_name="ROI",
            var_name="Type",
        ).set_index("Date")
        df_fin["Stock"] = f"{stock.fullname}_{stock.interval}"
        list_of_comparisons.append(df_fin)

    df_compare = pd.concat(list_of_comparisons)
    fig = px.box(df_compare, x="Stock", y="ROI", color="Type")
    x_axis = df_compare["Stock"].unique()
    fig.add_trace(
        go.Scatter(
            x=x_axis, y=[1] * len(x_axis), mode="lines+markers", name="profit line"
        )
    )
    time_of_completion = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")
    plot_path = str(
        Path(__file__).parent.parent
        / "plots"
        / f"plot_comparison_{time_of_completion}.html"
    )
    plot(fig, filename=plot_path, auto_open=True)
    sleep(1)

    return plot_path


def plot_strategy(
    stock, strategy = bollinger_bands, strategy_indicator="bb_bbli", price="Close", date_from=None
):
    """https://developer.mozilla.org/en-US/docs/Web/CSS/color_value colors for plotly"""

    df = strategy(stock.data)
    if date_from:
        df = df[date_from:]

    cur_price = [None] * (len(df) -1) + [stock.get_current_price()[price]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df[price], mode="lines", name=stock.fullname, line=dict(color="blue")
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=cur_price,
            mode="markers",
            name="Current price",
            marker=dict(color="red", size = 8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["bb_low"],
            mode="lines",
            name="bb_low",
            line=dict(color="chocolate"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["bb_high"],
            mode="lines",
            name="bb_high",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[price] * df[strategy_indicator].replace(0, np.nan),
            mode="markers",
            name="Strategy Buy",
            marker=dict(color="lime", size = 8),
        )
    )
    fig.update_layout(title=f"Prices of {stock.fullname}")
    time_of_completion = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")
    plot_path = str(
        Path(__file__).parent.parent
        / "plots"
        / f"plot_{stock.name}_{time_of_completion}.html"
    )

    plot(fig, filename=plot_path, auto_open=True)
    sleep(1)
    return plot_path




# =============================================================================
# Not yet usefull
#
# def plot_strategy_compare(data, strategy_indicator=["bb_bbli"], price = "Close" ):
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=data.index, y=data[price],
#                     mode='lines',
#                     name='price'))
#     for strategy in strategy_indicator:
#         fig.add_trace(go.Scatter(x=data.index, y=data[price]*data[strategy].replace(0, np.nan),
#                         mode='markers', name='markers'))
#     plot(fig, auto_open=True)
# =============================================================================
