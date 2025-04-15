#!/usr/bin/env python3
"""
简单的FreqAI模型训练脚本 - 代码运行版本

此脚本可以直接运行，不需要命令行参数，用于训练FreqAI模型和进行回测。
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# 添加freqtrade目录到Python路径
sys.path.append(str(Path.cwd()))

try:
    from freqtrade.commands import Arguments
    from freqtrade.commands.optimize_commands import start_backtesting
    from freqtrade.commands.data_commands import start_download_data
    from freqtrade.configuration import Configuration
except ImportError:
    logger.error("无法导入freqtrade模块，请确保脚本在freqtrade项目目录中运行。")
    sys.exit(1)


def download_data(config_file, pairs, timerange):
    """
    下载回测所需数据
    
    Args:
        config_file (str): 配置文件路径
        pairs (list): 交易对列表
        timerange (str): 时间范围
    """
    logger.info("开始下载数据...")
    

    # 使用正确的方式创建配置对象

    config = Configuration.from_files([config_file])
    print(config)
    # 下载数据
    start_download_data(config)
    
    logger.info("数据下载完成!")


def train_and_backtest(config_file, strategy_name, timerange):
    """
    训练模型并执行回测
    
    Args:
        config_file (str): 配置文件路径
        strategy_name (str): 策略名称
        timerange (str): 时间范围
        
    Returns:
        dict: 回测结果
    """
    logger.info(f"开始训练模型和回测，使用策略: {strategy_name}...")
    
    # 创建参数配置
    arguments = [
        '--config', config_file,
        'backtesting',
        '--strategy', strategy_name,
    ]
    
    if timerange:
        arguments.extend(['--timerange', timerange])
    
    # 使用正确的方式创建配置对象
    args = Arguments(arguments)
    config = Configuration.from_files([config_file])
    
    # 执行回测(会自动触发模型训练)
    result = start_backtesting(config)
    
    logger.info("模型训练和回测完成!")
    
    # 打印回测结果
    if result and 'strategy_comparison' in result and result['strategy_comparison']:
        stats = result['strategy_comparison'][0][strategy_name]
        
        logger.info("====== 回测结果摘要 ======")
        logger.info(f"总体收益: {stats['profit_total_abs']:.2f}")
        logger.info(f"总体收益率: {stats['profit_total']:.2f}%")
        logger.info(f"年化收益率: {stats.get('cagr_percentage', 0):.2f}%")
        logger.info(f"夏普比率: {stats.get('sharpe', 0):.2f}")
        logger.info(f"索提诺比率: {stats.get('sortino', 0):.2f}")
        logger.info(f"回撤: {stats.get('max_drawdown_percentage', 0):.2f}%")
        logger.info(f"交易总数: {stats['total_trades']}")
        logger.info(f"胜率: {stats.get('win_rate', 0) * 100:.2f}%")
    
    return result


def update_config(config_file, updates):
    """
    更新配置文件
    
    Args:
        config_file (str): 配置文件路径
        updates (dict): 要更新的配置参数
    """
    # 加载配置
    with open(config_file, 'r', encoding='utf-8') as file:
        config = json.load(file)
    
    # 递归更新配置
    def update_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                update_dict(d[k], v)
            else:
                d[k] = v
    
    update_dict(config, updates)
    
    # 保存更新后的配置
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)
    
    logger.info(f"已更新配置文件: {config_file}")


def main():
    """
    主函数
    """
    # ===== 用户配置部分 =====
    # 配置文件路径
    config_file = 'config.json'
    
    # 策略名称
    strategy_name = 'CustomFreqAIStrategy'
    
    # 交易对列表
    pairs = [
        "BTC/USDT:USDT",
        "ETH/USDT:USDT", 
        "BNB/USDT:USDT",
        "ADA/USDT:USDT",
        "SOL/USDT:USDT"
    ]
    
    # 计算时间范围 (例如：过去1年的数据)
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    timerange = f"{start_date}-{end_date}"
    
    # 修改配置参数 (可根据需要调整)
    config_updates = {
        "freqai": {
            "train_period_days": 60,  # 训练数据天数
            "backtest_period_days": 20,  # 回测数据天数
            "model_training_parameters": {
                "n_estimators": 300,
                "learning_rate": 0.03,
                "max_depth": 8
            }
        }
    }
    
    # ===== 执行部分 =====
    logger.info(f"使用配置文件: {config_file}")
    logger.info(f"使用策略: {strategy_name}")
    logger.info(f"时间范围: {timerange}")
    
    # 更新配置
    update_config(config_file, config_updates)
    
    # 下载数据
    download_data(config_file, pairs, timerange)
    
    # 训练模型并回测
    train_and_backtest(config_file, strategy_name, timerange)
    
    logger.info("脚本执行完成!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    except Exception as e:
        logger.error(f"错误: {str(e)}")
        sys.exit(1) 