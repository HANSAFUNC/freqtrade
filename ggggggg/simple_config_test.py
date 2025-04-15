#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

def check_config():
    """检查配置文件是否存在并可以被解析为JSON"""
    print(f"当前工作目录: {os.getcwd()}")
    
    # 尝试相对路径和绝对路径
    config_file = Path('user_data/config.json')
    current_dir = Path(__file__).parent.parent
    abs_config_file = current_dir / 'user_data/config.json'
    
    print(f"尝试相对路径: {config_file}")
    print(f"尝试绝对路径: {abs_config_file}")
    
    # 检查文件是否存在
    if config_file.exists():
        print(f"找到配置文件 (相对路径): {config_file}")
        actual_config_path = config_file
    elif abs_config_file.exists():
        print(f"找到配置文件 (绝对路径): {abs_config_file}")
        actual_config_path = abs_config_file
    else:
        print("错误: 配置文件不存在!")
        return False
    
    # 尝试解析JSON
    try:
        with open(actual_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("成功: 配置文件是有效的JSON格式")
        
        # 输出一些关键配置信息
        if 'exchange' in config:
            print(f"交易所: {config.get('exchange', {}).get('name')}")
            pairs = config.get('exchange', {}).get('pair_whitelist', [])
            print(f"交易对数量: {len(pairs)}")
            if pairs:
                print(f"样例交易对: {pairs[:3]}")
        
        if 'freqai' in config:
            print(f"FreqAI配置存在: 是")
            print(f"FreqAI启用状态: {config['freqai'].get('enabled')}")
            print(f"FreqAI模型: {config['freqai'].get('model_name', 'unknown')}")
        else:
            print("FreqAI配置存在: 否")
            
        return True
    except json.JSONDecodeError as e:
        print(f"错误: JSON格式无效 - {e}")
        return False
    except Exception as e:
        print(f"错误: 读取配置文件时发生未知错误 - {e}")
        return False

if __name__ == "__main__":
    success = check_config()
    if success:
        print("配置检查完成: 配置文件有效")
        sys.exit(0)
    else:
        print("配置检查完成: 配置文件无效或不存在")
        sys.exit(1) 