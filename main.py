"""To get daily updates on price fluctuation"""
import os
import shutil
from datetime import date, timedelta
from pathlib import Path

from transformations.Trading import (
    Stock,
    plot_compare_stocks,
    plot_strategy,
    bollinger_bands
)
from utilities.helper_functions import get_json_content
from utilities.screener_logger import logger

path_to_config = Path(__file__).parent.absolute() / "config/config.json"
config = get_json_content(path_to_config)
path_to_plots = Path(__file__).parent.absolute() / 'plots'


def run_general_information(interval = "1d"):
    logger.info("Gather information started")
    today = date.today()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=730)).strftime("%Y-%m-%d")

    stock_list = [Stock(stk,interval = interval) for stk in config["watchlist"]]
    logger.info(f"{[s.fullname for s in stock_list]} stock gathered as watchlist")

    logger.info("Plotting comparison of stocks")
    plot_compare_stocks(stock_list, date_from=start_date, date_to=end_date, period=365)
    for stock in stock_list:
        logger.info(f"Plotting {stock.fullname} strategy points")
        plot_strategy(
            stock, date_from=start_date
        )
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

def screener():
    logger.info("Screener started")
    logger.info("Screener finished")

if __name__ == "__main__":
    # screener()
    run_general_information()
    # clean_up()
