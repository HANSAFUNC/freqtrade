#!/usr/bin/env python3

import logging
from pathlib import Path
import numpy as np
from typing import Dict, Any

from freqtrade.configuration import Configuration
from freqtrade.freqai import FreqAI
from freqtrade.enums import RunMode
from freqtrade.resolvers import StrategyResolver
from freqtrade.freqai.prediction_models.LightGBMClassifier import LightGBMClassifier

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(config_file: str) -> None:
    """
    主函数：加载配置、初始化FreqAI并训练模型
    """
    # 加载配置
    logger.info(f"加载配置文件: {config_file}")
    config = Configuration.from_files([config_file])
    
    # 设置运行模式为干运行(不进行实际交易)
    config['runmode'] = RunMode.DRY_RUN
    
    # 初始化策略
    logger.info(f"初始化策略: {config.get('strategy')}")
    strategy = StrategyResolver.load_strategy(config)
    
    # 初始化FreqAI
    logger.info("初始化FreqAI")
    freqai = FreqAI(config)
    strategy.freqai = freqai
    
    # 设置交易对
    pair = config['exchange']['pair_whitelist'][0]
    logger.info(f"使用交易对: {pair}")
    
    # 创建数据目录
    data_path = Path(config['datadir'])
    data_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"数据目录: {data_path}")
    
    # 确保已下载数据
    logger.info("确保已下载时间范围内的数据")
    logger.info(f"时间范围: {config.get('timerange', '未指定')}")
    logger.info(f"时间周期: {config.get('timeframe', '未指定')}")
    logger.info(f"包含的时间周期: {config['freqai']['feature_parameters'].get('include_timeframes', [])}")
    
    # 训练模型
    logger.info("开始训练模型")
    freqai.start()
    
    logger.info("模型训练完成")
    
    # 模型评估（可选）
    # FreqAI会自动在训练过程中评估模型
    
    logger.info(f"训练日志保存在: {Path(config['datadir']).parent}/models/")

if __name__ == "__main__":
    config_file = 'freqai_config.json'
    main(config_file) 