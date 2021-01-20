import datetime
from pathlib import Path
from time import sleep

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from transformations.trading import bollinger_bands, return_on_hold, return_on_strategy
from utilities.screener_logger import logger

pd.options.mode.chained_assignment = None  # default='warn'

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
    stock,
    strategy=bollinger_bands,
    strategy_indicator="bb_bbli",
    price="Close",
    date_from=None,
):
    """https://developer.mozilla.org/en-US/docs/Web/CSS/color_value colors for plotly"""

    df = strategy(stock.data)
    if date_from:
        df = df[date_from:]

    cur_price = [None] * (len(df) - 1) + [stock.get_current_price()[price]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[price],
            mode="lines",
            name=stock.fullname,
            line=dict(color="blue"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=cur_price,
            mode="markers",
            name="Current price",
            marker=dict(color="red", size=8),
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
            marker=dict(color="lime", size=8),
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
