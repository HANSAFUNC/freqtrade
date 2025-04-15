#!/usr/bin/env python3
"""
FreqAI模型训练脚本

此脚本用于下载数据、训练FreqAI模型并进行回测，自动生成回测报告。
"""
import argparse
import logging
import sys
from pathlib import Path

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


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='FreqAI模型训练和回测工具')
    
    parser.add_argument(
        '--config', '-c',
        dest='config',
        default='user_data/config.json',
        help='指定配置文件 (默认: user_data/config.json)',
        type=str,
    )
    
    parser.add_argument(
        '--strategy', '-s',
        dest='strategy',
        default='CustomFreqAIStrategy',
        help='指定要使用的策略 (默认: CustomFreqAIStrategy)',
        type=str,
    )
    
    parser.add_argument(
        '--timerange', '-t',
        dest='timerange',
        default='',
        help='指定回测时间范围，格式如"20210101-20211231"',
        type=str,
    )
    
    parser.add_argument(
        '--pairs', '-p',
        dest='pairs',
        default='',
        help='指定交易对列表，用空格分隔',
        type=str,
    )
    
    parser.add_argument(
        '--download-only',
        dest='download_only',
        action='store_true',
        help='仅下载数据，不进行模型训练和回测',
    )
    
    return parser.parse_args()


def download_data(config_path, timerange, pairs):
    """
    下载回测所需数据
    """
    logger.info("开始下载数据...")
    
    args = [
        '--config', config_path,
        'download-data',
        '--timerange', timerange
    ]
    
    if pairs:
        args.extend(['--pairs', pairs])
    
    Arguments(args).parse_args()
    config = Configuration.from_arguments(Arguments(args))
    start_download_data(config)
    
    logger.info("数据下载完成!")


def train_and_backtest(config_path, strategy_name, timerange):
    """
    训练模型并执行回测
    """
    logger.info(f"开始训练模型和回测，使用策略: {strategy_name}...")
    
    args = [
        '--config', config_path,
        'backtesting',
        '--strategy', strategy_name,
    ]
    
    if timerange:
        args.extend(['--timerange', timerange])
    
    Arguments(args).parse_args()
    config = Configuration.from_arguments(Arguments(args))
    start_backtesting(config)
    
    logger.info("模型训练和回测完成!")


def main():
    """
    主函数
    """
    args = parse_args()
    
    # 获取配置
    config_path = args.config
    strategy_name = args.strategy
    timerange = args.timerange
    pairs = args.pairs
    
    logger.info(f"使用配置文件: {config_path}")
    logger.info(f"使用策略: {strategy_name}")
    
    if timerange:
        logger.info(f"时间范围: {timerange}")
    
    # 下载数据
    download_data(config_path, timerange, pairs)
    
    # 如果不是只下载数据，则开始训练和回测
    if not args.download_only:
        train_and_backtest(config_path, strategy_name, timerange)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    except Exception as e:
        logger.error(f"错误: {str(e)}")
        sys.exit(1) 