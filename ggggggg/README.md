# FreqAI交易机器人模型训练指南

本指南将帮助您使用FreqAI进行加密货币交易模型的训练和回测。

## 文件结构

- `config.json` - 配置文件，包含FreqAI和交易设置
- `strategies/CustomFreqAIStrategy.py` - 自定义策略文件，定义了特征工程和交易逻辑
- `freqaimodels/CustomXGBoostRegressor.py` - 自定义XGBoost模型，用于预测价格走势
- `train_model.py` - 命令行模式训练脚本，用于下载数据、训练模型和回测
- `run_freqai.py` - 代码运行模式脚本，无需命令行参数
- `train_freqai_model.py` - 简单的代码运行脚本，直接配置参数并运行

## 模型训练方式

您可以选择以下三种方式之一来训练FreqAI模型：

### 1. 直接运行 - 简单方式（推荐）

这是最简单的方式，直接在Python中设置参数并运行训练：

```bash
# 确保已激活FreqTrade环境
python user_data/train_freqai_model.py
```

您可以通过编辑脚本开头的配置部分来调整参数，例如交易对、时间范围、训练周期等。

### 2. 通过可定制脚本运行

如果您需要更多的控制和灵活性：

```bash
# 确保已激活FreqTrade环境
python user_data/run_freqai.py
```

在这个脚本中，您可以修改`run_mode`变量来选择执行模式：
- `download`: 仅下载数据
- `backtest`: 下载数据并进行训练和回测
- `live`: 使用训练好的模型进行实时交易

### 3. 命令行方式

适合习惯命令行界面的用户：

```bash
# 下载BTC、ETH等指定交易对的历史数据
python user_data/train_model.py --download-only --timerange 20210101-20220101 --pairs "BTC/USDT:USDT ETH/USDT:USDT BNB/USDT:USDT"

# 使用默认配置和策略进行模型训练和回测
python user_data/train_model.py --timerange 20210101-20220101
```

## 准备环境

确保已安装FreqTrade并激活环境：

```bash
# 如果尚未安装，请按照官方文档安装FreqTrade
cd freqtrade
source .env/bin/activate  # Linux/MacOS
# 或
.\.env\Scripts\activate  # Windows
```

## 配置说明

### config.json

配置文件中最重要的设置有：

- `freqai.train_period_days` - 训练数据的时间范围（天数）
- `freqai.backtest_period_days` - 回测数据的时间范围（天数）
- `freqai.feature_parameters.indicator_periods_candles` - 用于特征的指标周期
- `freqai.model_training_parameters` - 模型训练参数

可以根据需要调整这些参数来优化模型性能。

### 自定义策略

`CustomFreqAIStrategy.py` 包含：

- 特征工程函数（创建用于模型训练的技术指标）
- 目标变量定义（定义模型将预测的指标）
- 交易信号生成（根据预测结果创建买入/卖出信号）

## 进阶用法

### 自定义特征

要添加新的特征，请修改策略文件中的以下函数：

- `feature_engineering_expand_all` - 扩展到所有周期的特征
- `feature_engineering_expand_basic` - 基本特征
- `feature_engineering_standard` - 标准特征（不会自动扩展）

### 使用不同的模型

FreqTrade支持多种机器学习模型。要更改使用的模型，请在配置文件中修改：

```json
"freqai_model_name": "模型名称"
```

可用的模型包括：
- XGBoostRegressor (默认)
- LightGBMRegressor
- CatboostRegressor
- PyTorchMLPRegressor
- CustomXGBoostRegressor (我们的自定义模型)
- 等等

### 超参数调优

可以通过修改`config.json`中的`model_training_parameters`部分来优化模型的超参数。

您也可以编辑`train_freqai_model.py`脚本中的`config_updates`部分，无需直接修改配置文件：

```python
config_updates = {
    "freqai": {
        "model_training_parameters": {
            "n_estimators": 300,
            "learning_rate": 0.03,
            "max_depth": 8
        }
    }
}
```

## 故障排除

1. 如遇到内存错误，请尝试减少`train_period_days`或减少特征数量
2. 如果训练速度太慢，可以减少训练数据量或简化模型参数
3. 如果回测结果不理想，请尝试调整交易策略中的入场/出场条件

## 参考资源

- [FreqTrade官方文档](https://www.freqtrade.io/)
- [FreqAI文档](https://www.freqtrade.io/en/latest/freqai/) 