#!/usr/bin/env python3
"""
简单的数据下载脚本

此脚本使用命令行接口直接下载数据，避开自定义脚本中的逻辑
"""
import sys
import os
import traceback
from pathlib import Path

# 添加freqtrade目录到Python路径
sys.path.append(str(Path.cwd()))

try:
    # 导入命令行入口点
    from freqtrade.commands.data_commands import download_data_main
    print("FreqTrade模块导入成功")
except ImportError as e:
    print(f"无法导入freqtrade模块: {str(e)}")
    sys.exit(1)

def main():
    """主函数"""
    config_file = 'config.json'
    
    # 确保数据目录存在
    os.makedirs('user_data/data', exist_ok=True)
    
    # 使用简单的命令行参数
    args = [
        "--config", config_file,
        "--pairs", "BTC/USDT:USDT",
        "--days", "5",  # 只下载5天数据作为测试
        "-v"  # 使用verbose模式获取更多信息
    ]
    
    print(f"执行下载命令: freqtrade download-data {' '.join(args)}")
    
    try:
        # 直接使用命令行接口下载数据
        download_data_main(args)
        print("数据下载成功！")
    except Exception as e:
        print(f"下载数据时发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("用户中断，正在退出...")
    except Exception as e:
        print(f"错误: {str(e)}")
        traceback.print_exc()