"""To get daily updates on price fluctuation"""
from datetime import date, timedelta
from pathlib import Path

from transformations.Trading import (
    Stock,
    plot_compare_stocks,
    plot_strategy,
    bollinger_bands,
)
from utilities.helperfunctions import get_json_content
from utilities.screener_logger import logger

path_to_config = Path(__file__).parent.absolute() / "config/config.json"
config = get_json_content(path_to_config)

def run_screener():
    logger.error('testing')
    today = date.today()
    end_date = today.strftime("%Y-%d-%m")
    start_date = today - timedelta(days=365)

    stock_list = [Stock(stk) for stk in config["watchlist"]]
    plot_compare_stocks(stock_list, date_from=start_date, date_to=end_date, period=365)
    for stock in stock_list:
        plot_strategy(
            bollinger_bands(stock.data), name=stock.fullname, date_from=start_date
        )


if __name__ == "__main__":
    run_screener()
