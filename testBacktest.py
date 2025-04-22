from freqtrade.commands import (
start_backtesting,
start_trading,
start_webserver
)

from freqtrade.commands import Arguments
from freqtrade.main import main
def get_args(args):
    return Arguments(args).get_parsed_arg()

CURRENT_TEST_STRATEGY = "FreqaiExampleStrategy"

def trade():
    args = ["trade",
            "--config",
            "freqai_config.json",
            "--strategy",
            CURRENT_TEST_STRATEGY,
            "--freqaimodel",
            "LightGBMClassifier"]
    # start_webserver(get_args(args))
    # start_trading(get_args(args))
    main(args)

def backtesing():

    args = ["backtesting",
            "--config",
            "freqai_config2.json",
            "--strategy",
            CURRENT_TEST_STRATEGY,
           ]
    # start_webserver(get_args(args))
    # start_trading(get_args(args))
    main(args)


if __name__ == "__main__":
    backtesing()