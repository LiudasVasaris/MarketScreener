"""To get daily updates on price fluctuation"""
import os
import shutil
from datetime import date, timedelta
from pathlib import Path

from transformations.trading import Stock, bollinger_bands, buy_signal_filter
from utilities.helper_functions import get_json_content
from utilities.plotting_functions import plot_strategy, plot_compare_stocks
from utilities.screener_logger import logger

path_to_config = Path(__file__).parent.absolute() / "config/config.json"
config = get_json_content(path_to_config)
path_to_plots = Path(__file__).parent.absolute() / "plots"

interval_default = "1d"
signal_lag_default = 3

def run_general_information(stock_list):
    logger.info("Gather information started")
    today = date.today()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=730)).strftime("%Y-%m-%d")

    logger.info("Plotting comparison of stocks")
    plot_compare_stocks(stock_list, date_from=start_date, date_to=end_date, period=365)
    for stock in stock_list:
        logger.info(f"Plotting {stock.fullname} strategy points")
        plot_strategy(stock, date_from=start_date)
    logger.info("Gather information ended")


def clean_up():
    logger.info("Cleanup started")
    for filename in os.listdir(path_to_plots):
        filepath = os.path.join(path_to_plots, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)
    logger.info("Cleanup finished")


def screener(
    stock_list, strategy=bollinger_bands, strategy_indicator="bb_bbli", signal_lag=3
):
    logger.info("Screener started")
    screened_list = [
        stock
        for stock in stock_list
        if buy_signal_filter(stock, strategy, strategy_indicator, signal_lag)
    ]
    logger.info("Screener finished")
    return screened_list


def gather_stocks_from_watchlist(watchlist=config["watchlist"]):
    stock_list = [Stock(stk, interval=interval_default) for stk in watchlist]
    logger.info(f"{[s.fullname for s in stock_list]} stock gathered as watchlist")
    return stock_list


if __name__ == "__main__":
    stock_list = gather_stocks_from_watchlist()
    screened_stock_list = screener(stock_list,signal_lag=signal_lag_default)
    if screened_stock_list:
        run_general_information(screened_stock_list)
        clean_up()
