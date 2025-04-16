#!/usr/bin/env python3

import logging
import sys
from pathlib import Path
import json
from freqtrade.enums import RunMode
from freqtrade.configuration import TimeRange
# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("下载数据")
logger.disabled = True

def load_config(config_file='download_config.json'):
    """
    加载配置文件
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        sys.exit(1)

def download_data(config):
    """
    使用freqtrade API下载数据
    """
    try:
        from freqtrade.configuration import Configuration
        from freqtrade.data.history.history_utils import refresh_backtest_ohlcv_data
        from freqtrade.exchange import Exchange
        from freqtrade.resolvers import ExchangeResolver
        # from freqtrade.constants import Config
        # 确保数据目录存在
        data_dir = config.get('datadir', 'user_data/data')

        data_dir.mkdir(parents=True, exist_ok=True)

        # 要下载的交易对
        pairs = config['exchange']['pair_whitelist']

        # 要下载的时间周期
        timeframe = config.get('timeframe', '15m')
        timeframes = config.get('timeframes', [timeframe])

        # 时间范围
        timerange = config.get('timerange', None)
        config["runmode"] = RunMode.DRY_RUN
        # 交易所名称
        exchange_name = config['exchange']['name']

        # 交易模式
        trading_mode = config.get('trading_mode', 'spot')

        logger.info(f"开始从 {exchange_name} 下载数据:")
        logger.info(f"交易对: {pairs}")
        logger.info(f"时间周期: {timeframes}")
        logger.info(f"时间范围: {timerange}")
        logger.info(f"交易模式: {trading_mode}")

        timerange = TimeRange.parse_timerange(timerange)
        # 创建交易所对象
        exchange = ExchangeResolver.load_exchange(config, validate=False)

        # 下载数据
        refresh_backtest_ohlcv_data(
            datadir=data_dir,
            pairs=pairs,
            timeframes=timeframes,
            timerange=timerange,
            exchange=exchange,
            erase=False,
            data_format=config.get('dataformat_ohlcv', 'feather'),
            trading_mode=trading_mode
        )

        logger.info("数据下载完成!")
        return True
    except Exception as e:
        logger.error(f"下载数据失败: {e}")
        logger.info("尝试使用命令行下载数据:")

        # 构建命令行命令
        pairs_str = " ".join(config['exchange']['pair_whitelist'])
        timeframes_str = " ".join(config['freqai']['feature_parameters'].get('include_timeframes', [config.get('timeframe', '15m')]))
        exchange = config['exchange']['name']
        timerange = config.get('timerange', '')
        trading_mode = config.get('trading_mode', 'spot')

        cmd = (f"freqtrade download-data "
               f"--exchange {exchange} "
               f"--pairs {pairs_str} "
               f"--timeframes {timeframes_str} "
               f"--trading-mode {trading_mode}")

        if timerange:
            cmd += f" --timerange {timerange}"

        logger.info(f"请手动执行以下命令:")
        logger.info(cmd)
        return False

def main():
    """
    主函数
    """
    # 加载配置
    config = load_config()
    
    # 下载数据
    success = download_data(config)
    
    if not success:
        logger.info("脚本无法自动下载数据，请按照上面的提示手动下载。")
    else:
        logger.info("数据下载成功，现在可以运行FreqAI训练了。")

if __name__ == "__main__":
    main() 