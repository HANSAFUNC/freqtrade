#!/usr/bin/env python3
"""
FreqAI模型训练直接运行脚本

此脚本用于直接通过代码运行的方式下载数据、训练FreqAI模型并进行回测，
无需使用命令行参数。
"""
import logging
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json

# 检查Python版本和环境
current_python = sys.version.split()[0]
conda_env = os.environ.get('CONDA_DEFAULT_ENV')

print(f"当前Python版本: {current_python}")
if conda_env:
    print(f"当前conda环境: {conda_env}")
else:
    print("未检测到conda环境，可能使用的是标准Python环境")

if sys.version_info < (3, 10):
    print(f"错误: 当前Python版本为 {current_python}，FreqTrade要求Python 3.10或更高版本")
    if conda_env:
        print(f"您当前的conda环境是: {conda_env}")
        print("请创建一个使用Python 3.10+的新conda环境:")
        print("   conda create --name freqtrade_env python=3.10")
        print("   conda activate freqtrade_env")
        print("   pip install -e .")
    else:
        print("推荐使用conda创建新环境:")
        print("   conda create --name freqtrade python=3.10")
        print("   conda activate freqtrade")
    sys.exit(1)
else:
    print(f"Python版本检查通过: {current_python}")

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# 获取当前工作目录并将其添加到Python路径
# 检测当前脚本的运行路径
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# 获取FreqTrade根目录 - 如果脚本在user_data中，则向上一级
if SCRIPT_DIR.name == 'user_data':
    FREQTRADE_DIR = SCRIPT_DIR.parent
else:
    FREQTRADE_DIR = SCRIPT_DIR
    
# 设置工作目录为FreqTrade根目录
WORKING_DIR = FREQTRADE_DIR
sys.path.append(str(WORKING_DIR))
logger.info(f"脚本目录: {SCRIPT_DIR}")
logger.info(f"FreqTrade根目录: {FREQTRADE_DIR}")
logger.info(f"工作目录: {WORKING_DIR}")

try:
    logger.info("正在导入FreqTrade模块...")
    from freqtrade.commands import Arguments
    from freqtrade.commands.optimize_commands import start_backtesting
    from freqtrade.commands.data_commands import start_download_data
    from freqtrade.configuration import Configuration
    from freqtrade.enums import RunMode
    logger.info("FreqTrade模块导入成功")
except ImportError as e:
    logger.error(f"无法导入freqtrade模块: {str(e)}")
    if conda_env:
        logger.error(f"当前conda环境: {conda_env}，请确保在此环境中安装了freqtrade")
        logger.error("请运行: conda activate 您的环境名称")
        logger.error("然后运行: pip install -e .")
    else:
        logger.error("请确保已经安装了freqtrade及其依赖，或者运行 'pip install -e .' 进行安装")
    logger.error("如果问题仍然存在，尝试重新安装: 'pip install -r requirements.txt && pip install -r requirements-freqai.txt'")
    sys.exit(1)


def check_strategy_exists(strategy_name):
    """
    检查策略文件是否存在
    
    :param strategy_name: 策略名称
    :return: 是否存在
    """
    # 检查策略文件是否存在
    possible_paths = [
        FREQTRADE_DIR / "user_data" / "strategies" / f"{strategy_name}.py",
        FREQTRADE_DIR / "freqtrade" / "strategy" / f"{strategy_name}.py",
        FREQTRADE_DIR / "strategy" / f"{strategy_name}.py"
    ]
    
    found = False
    for path in possible_paths:
        if path.exists():
            logger.info(f"策略文件找到: {path}")
            found = True
            break
    
    if not found:
        logger.warning(f"找不到策略文件: {strategy_name}，检查了以下路径: {possible_paths}")
    
    return found


def check_environment():
    """
    执行最小环境检查，确保基本功能可用
    """
    logger.info("执行最小环境检查...")
    
    # 检查基本模块
    try:
        import freqtrade
        logger.info(f"找到FreqTrade模块")
        return True
    except ImportError:
        logger.error("找不到FreqTrade模块")
        return False


def print_config_summary(config):
    """
    打印配置文件的关键内容摘要
    
    :param config: 配置对象
    """
    logger.info("====== 配置文件摘要 ======")
    
    # 基本设置
    logger.info(f"交易模式: {config.get('trading_mode', '未设置')}")
    logger.info(f"保证金模式: {config.get('margin_mode', '未设置')}")
    logger.info(f"交易所: {config.get('exchange', {}).get('name', '未设置')}")
    logger.info(f"最大同时交易数: {config.get('max_open_trades', '未设置')}")
    logger.info(f"交易货币: {config.get('stake_currency', '未设置')}")
    logger.info(f"单笔交易金额: {config.get('stake_amount', '未设置')}")
    
    # 交易对
    pairs = config.get('exchange', {}).get('pair_whitelist', [])
    logger.info(f"交易对数量: {len(pairs)}")
    if pairs:
        logger.info(f"交易对示例: {', '.join(pairs[:3])}" + ("..." if len(pairs) > 3 else ""))
    
    # 时间框架
    logger.info(f"基础时间框架: {config.get('timeframe', '未设置')}")
    
    # FreqAI相关配置
    if 'freqai' in config:
        freqai_config = config.get('freqai', {})
        logger.info("FreqAI配置:")
        logger.info(f"  - 已启用: {freqai_config.get('enabled', False)}")
        logger.info(f"  - 模型名称: {freqai_config.get('freqai_model_name', '未设置')}")
        logger.info(f"  - 训练周期(天): {freqai_config.get('train_period_days', '未设置')}")
        logger.info(f"  - 回测周期(天): {freqai_config.get('backtest_period_days', '未设置')}")
        logger.info(f"  - 实时重训周期(小时): {freqai_config.get('live_retrain_hours', '未设置')}")
        
        # 特征参数
        feature_params = freqai_config.get('feature_parameters', {})
        if feature_params:
            timeframes = feature_params.get('include_timeframes', [])
            logger.info(f"  - 包含时间框架: {', '.join(timeframes) if timeframes else '未设置'}")
            
            corr_pairs = feature_params.get('include_corr_pairlist', [])
            logger.info(f"  - 相关交易对: {', '.join(corr_pairs) if corr_pairs else '未设置'}")
            
            logger.info(f"  - 标签周期K线数: {feature_params.get('label_period_candles', '未设置')}")
    else:
        logger.warning("配置中未找到FreqAI设置")
    
    logger.info("====== 配置摘要结束 ======")


def analyze_config_issues(config):
    """
    分析配置文件中可能存在的问题
    
    :param config: 配置对象
    :return: 问题列表
    """
    issues = []
    
    # 检查基本配置
    if not config.get('exchange', {}).get('name'):
        issues.append("未设置交易所名称")
    
    if not config.get('stake_currency'):
        issues.append("未设置交易货币(stake_currency)")
    
    if 'max_open_trades' not in config:
        issues.append("未设置最大同时交易数(max_open_trades)")
    
    # 检查交易对
    if not config.get('exchange', {}).get('pair_whitelist'):
        issues.append("交易对白名单为空")
    
    # 检查FreqAI配置
    if 'freqai' in config:
        freqai_config = config.get('freqai', {})
        
        # 检查是否启用
        if not freqai_config.get('enabled', False):
            issues.append("FreqAI未启用(freqai.enabled = false)")
        
        # 检查必要参数
        if not freqai_config.get('freqai_model_name'):
            issues.append("未指定FreqAI模型名称(freqai.freqai_model_name)")
        
        # 检查训练参数
        train_days = freqai_config.get('train_period_days')
        if not train_days:
            issues.append("未设置训练周期(freqai.train_period_days)")
        
        backtest_days = freqai_config.get('backtest_period_days')
        if not backtest_days:
            issues.append("未设置回测周期(freqai.backtest_period_days)")
        
        # 检查特征参数
        feature_params = freqai_config.get('feature_parameters', {})
        if not feature_params:
            issues.append("特征参数为空(freqai.feature_parameters)")
        else:
            if not feature_params.get('include_timeframes'):
                issues.append("未设置包含时间框架(freqai.feature_parameters.include_timeframes)")
            
            if 'label_period_candles' not in feature_params:
                issues.append("未设置标签周期K线数(freqai.feature_parameters.label_period_candles)")
    else:
        issues.append("配置中缺少FreqAI部分")
    
    return issues


def check_config(config_file):
    """
    检查配置文件是否存在并可读
    
    :param config_file: 配置文件路径
    :return: (是否可用, 配置对象)
    """
    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(config_file):
        # 首先尝试脚本所在目录
        config_path = SCRIPT_DIR / config_file
        if not config_path.exists():
            # 如果不存在，尝试freqtrade根目录/user_data
            config_path = FREQTRADE_DIR / "user_data" / config_file
    else:
        config_path = Path(config_file)
    
    logger.info(f"尝试加载配置文件: {config_path}")
    
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        return False, None
    
    try:
        logger.info(f"开始解析配置文件内容...")
        
        # 先检查文件是否为有效的JSON格式
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = f.read()
                # 尝试解析JSON
                json_config = json.loads(raw_config)
                logger.info("JSON格式验证通过")
        except json.JSONDecodeError as je:
            logger.error(f"配置文件不是有效的JSON格式: {je}")
            logger.error(f"错误位置: 第{je.lineno}行, 列{je.colno}")
            logger.error(f"错误内容: {je.msg}")
            return False, None
        except Exception as e:
            logger.error(f"读取配置文件时出错: {str(e)}")
            return False, None
        
        # 使用正确的方式创建配置对象
        logger.info("创建Arguments对象...")
        logger.info(f"最终下载参数: {' '.join(arguments)}")
        args = Arguments(arguments).get_parsed_arg()
        logger.info("从配置文件加载配置...")
        config = Configuration.from_files([config_path])
        
        # 打印配置摘要
        print_config_summary(config)
        
        # 分析配置问题
        issues = analyze_config_issues(config)
        if issues:
            logger.warning("配置文件存在以下问题:")
            for issue in issues:
                logger.warning(f" - {issue}")
        else:
            logger.info("配置文件检查通过，未发现明显问题")
        
        return True, config
    except Exception as e:
        logger.error(f"配置文件加载失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False, None


def download_data(config_file, pairs, timerange):
    """
    下载回测所需数据
    
    :param config_file: 配置文件路径
    :param pairs: 交易对列表
    :param timerange: 时间范围
    """
    logger.info("开始下载数据...")
    
    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(config_file):
        # 首先尝试脚本所在目录
        config_path = str(SCRIPT_DIR / config_file)
        if not Path(config_path).exists():
            # 如果不存在，尝试freqtrade根目录/user_data
            config_path = str(FREQTRADE_DIR / "user_data" / config_file)
    else:
        config_path = config_file
    
    # 创建参数配置
    arguments = [
        '--config', config_path,
        'download-data',
        '--timerange', timerange,
        # 增加详细输出
        '-v',
        # 添加期货模式
        '--trading-mode', 'futures',
    ]
    
    if pairs:
        # 使用空格分隔交易对列表，每个交易对作为独立参数
        arguments.extend(['--pairs'] + pairs)
    if timerange:
        arguments.extend(['--timerange', timerange])
    
    logger.info(f"下载参数: {' '.join(arguments)}")
    
    try:
        # 确保arguments中包含必要的参数
        if '--trading-mode' not in ' '.join(arguments):
            arguments.extend(['--trading-mode', 'futures'])
        
        # 创建数据目录
        data_dir = Path(FREQTRADE_DIR) / 'ggggggg' / 'user_data' / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加数据目录参数
        if '--datadir' not in ' '.join(arguments):
            arguments.extend(['--datadir', str(data_dir)])
        
        # 使用正确的方式创建配置对象
        logger.info("创建Arguments对象...")
        logger.info(f"最终下载参数: {' '.join(arguments)}")
        args = Arguments(arguments).get_parsed_arg()
        
        # 显示交易所和交易对信息
        exchange = config.get('exchange', {}).get('name', '未设置')
        logger.info(f"使用交易所 {exchange} 下载数据")
        
        pairs_whitelist = config.get('exchange', {}).get('pair_whitelist', [])
        if pairs_whitelist:
            logger.info(f"配置中的交易对白名单: {pairs_whitelist}")
        
        # 检查FreqAI所需的时间框架
        if 'freqai' in config:
            timeframes = config.get('freqai', {}).get('feature_parameters', {}).get('include_timeframes', [])
            if timeframes:
                logger.info(f"FreqAI需要的时间框架: {timeframes}")
                # 在命令中添加时间框架
                if '--timeframes' not in arguments:
                    timeframes_arg = ' '.join(timeframes)
                    arguments.extend(['--timeframes', timeframes_arg])
                    logger.info(f"自动添加时间框架到下载参数: {timeframes_arg}")
        
        # 下载数据
        logger.info("开始执行数据下载...")
        try:
            # 选项1: 使用start_download_data API
            try:
                start_download_data(args)
                logger.info("数据下载完成!")
                # 询问用户是否继续执行回测
                if input("数据下载已完成，是否继续执行回测? (y/n): ").lower() != 'y':
                    logger.info("用户选择退出，不执行回测")
                    return
            except Exception as api_error:
                logger.error(f"使用API下载数据失败: {str(api_error)}")
                logger.info("尝试使用命令行方式下载...")
                
                # 选项2: 构建完整命令并使用os.system执行
                data_dir = Path(FREQTRADE_DIR) / 'ggggggg' / 'user_data' / 'data'
                data_dir.mkdir(parents=True, exist_ok=True)
                
                cli_cmd = ' '.join(['freqtrade', 'download-data', 
                                  f'--config={config_path}',
                                  f'--datadir={data_dir}',
                                  '--trading-mode', 'futures',
                                  ] + 
                                  ([] if not pairs else ['--pairs'] + pairs) +
                                  (['--timerange', timerange] if timerange else []) +
                                  ['-v'])
                
                logger.info(f"执行命令: {cli_cmd}")
                exit_code = os.system(cli_cmd)
                
                if exit_code != 0:
                    logger.error(f"命令行下载失败，退出代码: {exit_code}")
                else:
                    logger.info("数据下载完成!")
        except Exception as e:
            logger.error(f"数据下载过程出现错误: {str(e)}")
            logger.error("详细错误信息:")
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"下载数据准备阶段出现错误: {str(e)}")
        logger.error("详细错误信息:")
        logger.error(traceback.format_exc())


def train_and_backtest(config_file, strategy_name, timerange):
    """
    训练模型并执行回测
    
    :param config_file: 配置文件路径
    :param strategy_name: 策略名称
    :param timerange: 时间范围
    """
    logger.info(f"开始训练模型和回测，使用策略: {strategy_name}...")
    
    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(config_file):
        # 首先尝试脚本所在目录
        config_path = str(SCRIPT_DIR / config_file)
        if not Path(config_path).exists():
            # 如果不存在，尝试freqtrade根目录/user_data
            config_path = str(FREQTRADE_DIR / "user_data" / config_file)
    else:
        config_path = config_file
    
    # 创建参数配置
    arguments = [
        '--config', config_path,
        'backtesting',
        '--strategy', strategy_name,
    ]
    
    if timerange:
        arguments.extend(['--timerange', timerange])
    
    logger.info(f"回测参数: {' '.join(arguments)}")
    
    try:
        # 使用正确的方式创建配置对象
        args = Arguments(arguments).get_parsed_arg()
        
        # 执行回测(会自动触发模型训练)
        start_backtesting(args)
        
        logger.info("模型训练和回测完成!")
    except Exception as e:
        logger.error(f"训练和回测时发生错误: {str(e)}")
        logger.error(traceback.format_exc())


def run_freqai_live(config_file, strategy_name):
    """
    启动实时交易模式
    
    :param config_file: 配置文件路径
    :param strategy_name: 策略名称
    """
    logger.info(f"启动实时交易，使用策略: {strategy_name}...")
    
    # 如果是相对路径，转为绝对路径
    if not os.path.isabs(config_file):
        # 首先尝试脚本所在目录
        config_path = str(SCRIPT_DIR / config_file)
        if not Path(config_path).exists():
            # 如果不存在，尝试freqtrade根目录/user_data
            config_path = str(FREQTRADE_DIR / "user_data" / config_file)
    else:
        config_path = config_file
    
    # 创建参数配置
    arguments = [
        '--config', config_path,
        'trade',
        '--strategy', strategy_name,
    ]
    
    try:
        # 使用正确的方式创建配置对象
        args = Arguments(arguments).get_parsed_arg()
        
        # 导入并启动Bot实例
        from freqtrade.main import main
        main(args)
    except Exception as e:
        logger.error(f"启动实时交易时发生错误: {str(e)}")
        logger.error(traceback.format_exc())


def create_userdir():
    """
    创建FreqTrade用户数据目录
    """
    userdir = Path(FREQTRADE_DIR) / 'user_data'
    logger.info(f"确保用户数据目录存在: {userdir}")
    
    # 检查用户目录是否存在
    if userdir.exists():
        logger.info("用户目录已存在")
        return True
    
    # 尝试创建用户目录
    try:
        logger.info("创建用户目录...")
        cmd = ['freqtrade', 'create-userdir', '--userdir', str(userdir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"创建用户目录失败: {result.stderr}")
            return False
            
        logger.info("用户目录创建成功")
        return True
    except Exception as e:
        logger.error(f"创建用户目录时出错: {str(e)}")
        return False


def run_command(run_mode, config_file, strategy_name, pairs=None, timerange=None):
    """
    运行FreqTrade命令
    """
    if not Path(config_file).is_file():
        # 尝试在user_data目录下查找
        user_data_config = FREQTRADE_DIR / 'user_data' / config_file
        if user_data_config.is_file():
            config_file = str(user_data_config)
        else:
            logger.error(f"配置文件 {config_file} 不存在!")
            logger.error(f"当前工作目录: {os.getcwd()}")
            logger.error(f"尝试查找: {Path(config_file).absolute()}")
            logger.error(f"以及: {user_data_config}")
            logger.error("请检查配置文件路径是否正确")
            return False
    
    # 确保数据目录存在
    data_dir = Path(FREQTRADE_DIR) / 'ggggggg' / 'user_data' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"确保数据目录存在: {data_dir}")
    
    # 基本命令
    cmd = [
        'freqtrade',
        f'--config', config_file,
        # 不使用--userdir参数，让FreqTrade使用默认路径
    ]

    # 根据运行模式添加子命令
    if run_mode == 'download':
        cmd.insert(1, 'download-data')
        # 添加明确的数据目录路径，避免重复的user_data目录
        cmd.extend(['--datadir', str(data_dir)])
        
        # 添加时间框架，分开指定每个时间框架
        cmd.extend(['--timeframes', '5m', '15m', '1h'])
        
        # 指定交易模式为期货
        cmd.extend(['--trading-mode', 'futures'])
        
        # 增加详细输出，以便查看进度
        cmd.append('-v')
        
        if pairs:
            # 使用空格分隔交易对列表，每个交易对作为独立参数
            cmd.extend(['--pairs'] + pairs)
        if timerange:
            cmd.extend(['--timerange', timerange])
    elif run_mode == 'backtest':
        cmd.insert(1, 'backtesting')
        # 添加数据目录
        cmd.extend(['--datadir', str(data_dir) + "/okx/futures"])
        
        # 回测时需要指定策略
        if strategy_name:
            cmd.extend(['--strategy', strategy_name])
        if pairs:
            # 使用空格分隔交易对列表，每个交易对作为独立参数
            cmd.extend(['--pairs'] + pairs)
        if timerange:
            cmd.extend(['--timerange', timerange])
    elif run_mode == 'live':
        cmd.insert(1, 'trade')
        # 实时交易时需要指定策略
        if strategy_name:
            cmd.extend(['--strategy', strategy_name])
    else:
        logger.error(f"未知的运行模式: {run_mode}")
        return False
    
    # 执行命令
    cmd_str = ' '.join([str(c) for c in cmd])
    logger.info(f"执行命令: {cmd_str}")
    
    try:
        # 使用os.system直接执行命令，输出会直接显示在控制台
        logger.info("开始执行命令，请等待...")
        exit_code = os.system(cmd_str)
        
        if exit_code != 0:
            logger.error(f"命令执行失败，退出代码: {exit_code}")
            return False
        
        logger.info("命令执行成功!")
        
        # 如果是下载数据模式，询问用户是否继续
        if run_mode == 'download':
            if input("数据下载已完成，是否继续执行回测? (y/n): ").lower() != 'y':
                logger.info("用户选择退出，不执行回测")
                return True
                
        return True
    except Exception as e:
        logger.error(f"执行命令时发生异常: {str(e)}")
        return False


def main():
    """
    主函数：运行FreqAI
    """
    # 执行最小环境检查
    check_environment()
    
    # 用户配置
    config_file = 'config.json'  # 配置文件路径
    strategy_name = 'CustomFreqAIStrategy'  # 策略名称
    pairs = ['BTC/USDT:USDT', 'ETH/USDT:USDT']  # 交易对
    timerange = '20210101-20210201'  # 时间范围
    run_mode = 'backtest'  # 运行模式: 'download', 'backtest', 'live'
    
    # 确保配置文件路径正确
    if not os.path.isabs(config_file):
        # 首先检查当前目录
        if os.path.isfile(config_file):
            config_file = os.path.abspath(config_file)
        else:
            # 检查user_data目录
            user_data_config = FREQTRADE_DIR / 'user_data' / config_file
            if user_data_config.exists():
                config_file = str(user_data_config)
            else:
                logger.error(f"配置文件 {config_file} 未找到")
                return False
    
    logger.info(f"使用配置文件: {config_file}")
    
    # 加载配置文件（仅为验证）
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"配置文件已成功加载: {config_file}")
        
        # 打印关键配置信息
        logger.info(f"交易所: {config.get('exchange', {}).get('name', '未指定')}")
        
        # 检查交易对列表
        exchange_config = config.get('exchange', {})
        if 'pair_whitelist' in exchange_config:
            pairs_list = exchange_config['pair_whitelist']
            logger.info(f"配置中的交易对: {', '.join(pairs_list[:5])}{'...' if len(pairs_list) > 5 else ''}")
        
        if 'freqai' in config:
            logger.info("FreqAI 功能已启用")
            if 'identifier' in config['freqai']:
                logger.info(f"FreqAI 标识符: {config['freqai']['identifier']}")
    except FileNotFoundError:
        logger.error(f"配置文件 {config_file} 未找到")
        return False
    except json.JSONDecodeError:
        logger.error(f"配置文件 {config_file} 不是有效的JSON格式")
        return False
    except Exception as e:
        logger.error(f"加载配置文件时发生错误: {e}")
        logger.error(traceback.format_exc())
        return False
    
    # 运行下载数据命令（如果需要）
    if run_mode == 'backtest' and input("是否需要先下载数据? (y/n): ").lower() == 'y':
        # 确保用户目录存在
        if not create_userdir():
            logger.error("无法创建用户目录，终止数据下载")
            return False
            
        # 确保数据目录存在
        data_dir = Path(FREQTRADE_DIR) / 'ggggggg' / 'user_data' / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"确保数据目录存在: {data_dir}")
            
        # 尝试直接使用官方推荐的命令行方式下载数据
        logger.info("使用标准命令行方式下载数据...")
        
        # 构建标准下载命令
        download_cmd = [
            'freqtrade', 'download-data',
            '--config', config_file,
            '--datadir', str(data_dir),  # 明确指定数据目录
            '--timeframes', '5m', '15m', '1h',  # 使用固定的时间框架参数
            '--trading-mode', 'futures',  # 指定交易模式为期货
            '-v',  # 增加详细输出以便查看进度
        ]
        
        if pairs:
            download_cmd.extend(['--pairs'] + pairs)
        
        if timerange:
            download_cmd.extend(['--timerange', timerange])
            
        try:
            # 将命令转换为字符串
            cmd_str = ' '.join([str(cmd) for cmd in download_cmd])
            logger.info(f"执行命令: {cmd_str}")
            
            # 使用os.system直接执行命令，输出会显示在控制台
            logger.info("开始下载数据，请等待...")
            exit_code = os.system(cmd_str)
            
            if exit_code != 0:
                logger.error(f"标准命令下载失败，退出代码: {exit_code}")
                logger.error("尝试备用方法...")
                if not run_command('download', config_file, strategy_name, pairs, timerange):
                    logger.error("数据下载失败，终止回测")
                    return False
            else:
                logger.info("数据下载成功!")
                # 询问用户是否继续
                if input("数据下载已完成，是否继续执行回测? (y/n): ").lower() != 'y':
                    logger.info("用户选择退出，不执行回测")
                    return True
        except Exception as e:
            logger.error(f"执行下载命令时出错: {str(e)}")
            logger.error("尝试备用方法...")
            if not run_command('download', config_file, strategy_name, pairs, timerange):
                logger.error("数据下载失败，终止回测")
                return False
    
    # 运行主命令
    success = run_command(run_mode, config_file, strategy_name, pairs, timerange)
    
    if success:
        logger.info(f"{run_mode.title()} 命令执行成功!")
    else:
        logger.error(f"{run_mode.title()} 命令执行失败.")
    
    return success


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    except Exception as e:
        logger.error(f"错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 