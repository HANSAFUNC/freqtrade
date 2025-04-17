import os
from pathlib import Path
# 添加nest_asyncio支持，解决Jupyter中的事件循环冲突
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("已应用nest_asyncio解决事件循环嵌套问题")
except ImportError:
    print("警告: 未安装nest_asyncio，在Jupyter中可能出现事件循环冲突。请运行 pip install nest_asyncio")


# Change directory
# Modify this cell to insure that the output shows the correct path.
# Define all paths relative to the project root shown in the cell output
project_root = "somedir/freqtrade"
i = 0
try:
    os.chdir(project_root)
    if not Path("LICENSE").is_file():
        i = 0
        while i < 4 and (not Path("LICENSE").is_file()):
            os.chdir(Path(Path.cwd(), "../"))
            i += 1
        project_root = Path.cwd()
except FileNotFoundError:
    print("Please define the project root relative to the current directory")
print(Path.cwd())


def main():

    from freqtrade.configuration import Configuration
    from download_data import download_data

    # Customize these according to your needs.

    # Initialize empty configuration object
    config = Configuration.from_files([Path.cwd()/"freqai_config.json"])
    print(config)

    # 下载数据
    success = download_data(config)
    if not success:
        print("脚本无法自动下载数据，请按照上面的提示手动下载。")
    else:
        print("数据下载成功，现在可以运行FreqAI训练了。")
    # print('数据下载完成！')
    # Define some constants
    config["timeframe"] = "15m"
    # Name of the strategy class
    # config["strategy"] = "SampleStrategy"
    # Location of the data
    data_location = config["datadir"]
    # Pair to analyze - Only use one pair here
    pair = "BTC/USDT"

    # Load data using values set above
    from freqtrade.data.history import load_pair_history
    from freqtrade.enums import CandleType
    from freqtrade.configuration import TimeRange
    # 要下载的时间周期
    timeframe = config.get('timeframe', '15m')
    timeframes = config.get('timeframes', [timeframe])

    # 时间范围
    timerange = "20230120-20250401"

    timerange = TimeRange.parse_timerange(timerange)
    candles = load_pair_history(
        datadir=data_location,
        timeframe=timeframe,
        timerange=timerange,
        pair=pair,
        data_format="feather",  # Make sure to update this to your data
        candle_type=CandleType.SPOT,
    )

    # Confirm success
    print(f"Loaded {len(candles)} rows of data for {pair} from {data_location}")
    candles.head(100)
    # print(candles.head(100))


    # Load strategy using values set above
    from freqtrade.data.dataprovider import DataProvider
    from freqtrade.resolvers import StrategyResolver

    from freqtrade.resolvers import ExchangeResolver
    exchange = ExchangeResolver.load_exchange(config, validate=False)
    strategy = StrategyResolver.load_strategy(config)
    strategy.dp = DataProvider(config,exchange)
    strategy.ft_bot_start()

    # Generate buy/sell signals using strategy
    df = strategy.analyze_ticker(candles, {"pair": pair})
    df.tail()

if __name__ == "__main__":
    main()