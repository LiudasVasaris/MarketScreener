"""To get daily updates on price fluctuation"""
from datetime import date, timedelta
from pathlib import Path

from transformations.Trading import (
    Stock,
    plot_compare_stocks,
    plot_strategy,
    bollinger_bands,
)
from utilities.helper_functions import get_json_content
from utilities.screener_logger import logger

path_to_config = Path(__file__).parent.absolute() / "config/config.json"
config = get_json_content(path_to_config)


def run_general_information():
    logger.info("Gather information started")
    today = date.today()
    end_date = today.strftime("%Y-%m-%d")
    start_date = today - timedelta(days=365)

    stock_list = [Stock(stk) for stk in config["watchlist"]]
    logger.info(f"{[s.name for s in stock_list]} stock gathered as watchlist")

    logger.info("Plotting comparison of stocks")
    plot_compare_stocks(stock_list, date_from=start_date, date_to=end_date, period=365)
    for stock in stock_list:
        logger.info(f"Plotting {stock.fullname} strategy points")
        plot_strategy(
            bollinger_bands(stock.data), name=stock.fullname, date_from=start_date
        )
    logger.info("Gather information ended")


if __name__ == "__main__":
    run_general_information()
