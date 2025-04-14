#!/usr/bin/env python3
"""
配置文件测试脚本

此脚本用于测试FreqTrade配置文件加载是否正常
"""
import sys
import traceback
from pathlib import Path

# 添加freqtrade目录到Python路径
sys.path.append(str(Path.cwd()))

try:
    from freqtrade.configuration import Configuration
    print("FreqTrade模块导入成功")
except ImportError as e:
    print(f"无法导入freqtrade模块: {str(e)}")
    sys.exit(1)

def test_config(config_file):
    """测试配置文件加载"""
    print(f"正在测试配置文件: {config_file}")
    
    # 1. 检查文件是否存在
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        return False
    
    print(f"配置文件存在: {config_file}")
    
    # 2. 尝试读取文件内容
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"成功读取配置文件内容，大小: {len(content)} 字节")
            # 打印前100个字符作为预览
            print(f"内容预览: {content[:100]}...")
    except Exception as e:
        print(f"读取配置文件时发生错误: {str(e)}")
        traceback.print_exc()
        return False
    
    # 3. 尝试解析JSON
    try:
        import json
        json_content = json.loads(content)
        print("JSON解析成功")
        
        # 检查关键配置项
        if 'exchange' not in json_content:
            print("警告: 配置中缺少'exchange'部分")
        else:
            print(f"交易所设置: {json_content['exchange']['name']}")
        
        if 'stake_currency' not in json_content:
            print("警告: 配置中缺少'stake_currency'")
        else:
            print(f"交易币种: {json_content['stake_currency']}")
        
        if 'freqai' not in json_content:
            print("警告: 配置中缺少'freqai'部分，这对于FreqAI训练是必需的")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {str(e)}")
        print(f"错误位置附近的内容: {content[max(0, e.pos-20):e.pos+20]}")
        return False
    except Exception as e:
        print(f"处理JSON时发生错误: {str(e)}")
        traceback.print_exc()
        return False
    
    # 4. 使用Configuration.from_files加载
    try:
        print("尝试使用Configuration.from_files加载配置...")
        config = Configuration.from_files([config_file])
        print("配置文件加载成功!")
        
        # 额外检查重要配置项
        required_keys = ['dry_run', 'max_open_trades', 'stake_currency', 'stake_amount', 'exchange']
        for key in required_keys:
            if key not in config:
                print(f"警告: 配置中缺少关键项: {key}")
        
        return True
    except Exception as e:
        print(f"使用Configuration加载配置文件时发生错误: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    config_file = 'config.json'
    success = test_config(config_file)
    
    if success:
        print("\n配置文件测试通过! ✅")
    else:
        print("\n配置文件测试失败! ❌")
        
    # 尝试使用命令执行简单下载任务
    if success:
        try:
            print("\n尝试使用直接方法下载数据...")
            from freqtrade.commands.data_commands import download_data_main
            args = ["--config", config_file, "--pairs", "BTC/USDT:USDT", "--days", "5"]
            download_data_main(args)
            print("下载命令执行成功!")
        except Exception as e:
            print(f"下载数据时发生错误: {str(e)}")
            traceback.print_exc() 