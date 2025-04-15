#!/usr/bin/env python3
"""
配置文件检查和修复工具

此脚本检查FreqTrade配置文件中的常见问题并尝试修复它们
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def check_and_fix_config(config_file):
    """检查并修复配置文件"""
    print(f"检查配置文件: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在: {config_file}")
        return False
    
    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析JSON
        try:
            config = json.loads(content)
            print("JSON格式正确")
        except json.JSONDecodeError as e:
            print(f"JSON格式错误: {e}")
            print(f"错误位置附近的内容: {content[max(0, e.pos-20):e.pos+20]}")
            return False
        
        # 备份原始配置
        backup_file = f"{config_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建配置文件备份: {backup_file}")
        
        # 检查并修复常见问题
        modified = False
        
        # 1. 检查必需字段
        required_fields = ['exchange', 'stake_currency', 'stake_amount', 'max_open_trades', 'dry_run']
        for field in required_fields:
            if field not in config:
                if field == 'exchange':
                    config[field] = {
                        "name": "binance",
                        "key": "",
                        "secret": "",
                        "ccxt_config": {},
                        "ccxt_async_config": {},
                        "pair_whitelist": ["BTC/USDT:USDT"],
                        "pair_blacklist": []
                    }
                elif field == 'stake_currency':
                    config[field] = "USDT"
                elif field == 'stake_amount':
                    config[field] = 100
                elif field == 'max_open_trades':
                    config[field] = 5
                elif field == 'dry_run':
                    config[field] = True
                print(f"添加了缺少的字段: {field}")
                modified = True
        
        # 2. 检查FreqAI部分
        if 'freqai' not in config:
            print("添加缺少的FreqAI配置部分")
            config['freqai'] = {
                "enabled": True,
                "purge_old_models": 2,
                "train_period_days": 30,
                "backtest_period_days": 10,
                "identifier": "crypto_predictor_v1",
                "feature_parameters": {
                    "include_timeframes": ["5m", "15m", "1h"],
                    "include_corr_pairlist": ["BTC/USDT:USDT", "ETH/USDT:USDT"],
                    "label_period_candles": 24,
                    "include_shifted_candles": 2,
                    "DI_threshold": 0.9,
                    "weight_factor": 0.9,
                    "principal_component_analysis": False,
                    "use_SVM_to_remove_outliers": True,
                    "indicator_periods_candles": [10, 20, 30],
                    "plot_feature_importances": 5
                },
                "data_split_parameters": {
                    "test_size": 0.25,
                    "random_state": 42,
                    "shuffle": True
                },
                "model_training_parameters": {
                    "n_estimators": 400,
                    "learning_rate": 0.025,
                    "max_depth": 8,
                    "gamma": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "reg_alpha": 0.02,
                    "reg_lambda": 0.05,
                    "eval_metric": "mae"
                },
                "freqai_model_name": "XGBoostRegressor"
            }
            modified = True
        
        # 3. 检查交易模式配置
        if config.get('trading_mode') == 'futures' and config.get('margin_mode') not in ['isolated', 'cross']:
            print("在futures模式下添加margin_mode")
            config['margin_mode'] = 'isolated'
            modified = True
        
        # 保存修改后的配置
        if modified:
            print("配置已修改，保存新配置...")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print("配置已保存")
        else:
            print("配置文件没有需要修改的地方")
        
        return True
    except Exception as e:
        print(f"检查配置时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    config_file = 'config.json'
    check_and_fix_config(config_file)

if __name__ == "__main__":
    main() 