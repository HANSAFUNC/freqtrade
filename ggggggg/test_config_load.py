#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

# 添加父目录到系统路径以便导入freqtrade模块
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))
print(f"添加路径: {current_dir}")
print(f"当前工作目录: {os.getcwd()}")

try:
    print("开始导入freqtrade模块...")
    from freqtrade.configuration import Configuration
    from freqtrade.constants import Config
    from freqtrade.exceptions import ConfigException
    print("freqtrade模块导入成功")
    
    config_file = Path('user_data/config.json')
    abs_config_file = current_dir / 'user_data/config.json'
    
    print(f"尝试加载配置文件: {config_file}")
    print(f"配置文件绝对路径: {abs_config_file}")
    print(f"配置文件存在: {config_file.exists() or abs_config_file.exists()}")
    
    # 检查用哪个路径可以找到配置文件
    actual_config_path = config_file if config_file.exists() else abs_config_file
    
    # 尝试直接用json加载配置文件以验证JSON格式
    try:
        with open(actual_config_path) as f:
            json_config = json.load(f)
        print("JSON格式解析成功")
        print(f"配置文件包含以下键: {list(json_config.keys())}")
    except json.JSONDecodeError as e:
        print(f"JSON格式错误: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"无法找到配置文件: {actual_config_path}")
        sys.exit(1)
    
    # 使用freqtrade的Configuration加载配置
    try:
        print(f"使用freqtrade加载配置文件: {actual_config_path}")
        configuration = Configuration(["--config", str(actual_config_path)])
        config = configuration.get_config()
        print("配置文件加载成功")
        print(f"交易所名称: {config.get('exchange', {}).get('name')}")
        print(f"交易对列表: {config.get('exchange', {}).get('pair_whitelist')}")
        
        # 检查关键配置部分
        if 'freqai' in config:
            print("找到FreqAI配置")
            print(f"FreqAI启用状态: {config['freqai'].get('enabled')}")
            print(f"FreqAI模型名称: {config['freqai'].get('freqai_model_name')}")
        
        print("配置文件测试完成，一切正常！")
        
    except ConfigException as e:
        print(f"配置异常: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"其他异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装freqtrade") 
    sys.exit(1) 