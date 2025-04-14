#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("下载数据")

def load_config(config_file='freqai_config.json'):
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

def main():
    """
    主函数 - 直接使用系统命令调用freqtrade
    """
    # 加载配置
    config = load_config()
    
    # 构建命令
    pairs_str = " ".join(config['exchange']['pair_whitelist'])
    timeframes_str = " ".join(config['freqai']['feature_parameters'].get('include_timeframes', [config.get('timeframe', '15m')]))
    exchange = config['exchange']['name']
    timerange = config.get('timerange', '')
    trading_mode = config.get('trading_mode', 'spot')
    
    cmd = f"freqtrade download-data --exchange {exchange} --pairs {pairs_str} --timeframes {timeframes_str} --trading-mode {trading_mode}"
    
    if timerange:
        cmd += f" --timerange {timerange}"
    
    # 输出命令
    logger.info(f"执行命令: {cmd}")
    
    # 运行命令
    logger.info("开始下载数据...")
    exit_code = os.system(cmd)
    
    if exit_code == 0:
        logger.info("数据下载成功！")
        logger.info("现在可以运行FreqAI训练了。")
    else:
        logger.error(f"数据下载失败，返回代码: {exit_code}")
        logger.error("请确保已正确安装并激活freqtrade环境，然后手动执行以下命令:")
        logger.error(cmd)

if __name__ == "__main__":
    main() 