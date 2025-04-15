import logging
from functools import reduce

import numpy as np
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IStrategy, merge_informative_pair


logger = logging.getLogger(__name__)


class CustomFreqAIStrategy(IStrategy):
    """
    自定义FreqAI策略，使用XGBoost模型进行加密货币价格趋势预测
    
    该策略利用多种技术指标和时间特征，结合FreqAI的机器学习功能
    来预测短期价格走势并进行交易决策。
    """

    minimal_roi = {
        "0": 0.05,
        "60": 0.03,
        "120": 0.02,
        "240": 0.01
    }

    plot_config = {
        "main_plot": {
            "sma_50": {"color": "blue"},
            "sma_200": {"color": "red"}
        },
        "subplots": {
            "&-s_close": {"&-s_close": {"color": "green"}},
            "do_predict": {"do_predict": {"color": "brown"}},
            "prediction_probability": {"prediction_probability": {"color": "purple"}}
        },
    }

    process_only_new_candles = True
    stoploss = -0.05
    use_exit_signal = True
    startup_candle_count: int = 200
    can_short = True

    # 选择使用的FreqAI模型
    freqai_model_name = "XGBoostRegressor"

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        扩展特征，将自动应用到所有配置的指标周期、时间框架和相关对
        """
        # 技术指标
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-cci-period"] = ta.CCI(dataframe, timeperiod=period)
        dataframe["%-macd-period"], dataframe["%-macdsignal-period"], _ = ta.MACD(
            dataframe, fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # 移动平均线
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        
        # 布林带
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=period, stds=2.2
        )
        dataframe["%-bb_lower-period"] = bollinger["lower"]
        dataframe["%-bb_middle-period"] = bollinger["mid"]
        dataframe["%-bb_upper-period"] = bollinger["upper"]
        dataframe["%-bb_width-period"] = (
            dataframe["%-bb_upper-period"] - dataframe["%-bb_lower-period"]
        ) / dataframe["%-bb_middle-period"]
        dataframe["%-close-bb_lower-period"] = dataframe["close"] / dataframe["%-bb_lower-period"]

        # 动量指标
        dataframe["%-roc-period"] = ta.ROC(dataframe, timeperiod=period)
        dataframe["%-mom-period"] = ta.MOM(dataframe, timeperiod=period)
        
        # ATR - 平均真实范围
        dataframe["%-atr-period"] = ta.ATR(dataframe, timeperiod=period)
        
        # 成交量指标
        dataframe["%-obv-period"] = ta.OBV(dataframe)
        dataframe["%-relative_volume-period"] = (
            dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        )
        
        # 价格变化指标
        dataframe["%-price_change-period"] = dataframe["close"].pct_change(period)
        
        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        基本特征工程，会扩展到配置的时间框架、偏移蜡烛和相关对
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        
        # 价格与移动平均线的关系
        dataframe["%-price_over_sma50"] = dataframe["close"] / ta.SMA(dataframe, timeperiod=50)
        dataframe["%-price_over_sma200"] = dataframe["close"] / ta.SMA(dataframe, timeperiod=200)
        
        # 波动率
        dataframe["%-volatility_14"] = dataframe["close"].rolling(14).std()
        
        # 最高价和最低价与收盘价的关系
        dataframe["%-high_over_close"] = dataframe["high"] / dataframe["close"]
        dataframe["%-low_over_close"] = dataframe["low"] / dataframe["close"]
        
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        标准特征工程，不会自动扩展
        """
        # 时间特征
        dataframe["%-day_of_week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour_of_day"] = dataframe["date"].dt.hour
        dataframe["%-minute_of_hour"] = dataframe["date"].dt.minute
        dataframe["%-is_weekend"] = dataframe["date"].dt.dayofweek.isin([5, 6]).astype(int)
        
        # 趋势指标
        dataframe["sma_50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["sma_200"] = ta.SMA(dataframe, timeperiod=200)
        dataframe["%-trend_sma"] = (dataframe["sma_50"] > dataframe["sma_200"]).astype(int)
        
        # 连续上涨/下跌的天数
        dataframe["%-price_up"] = (dataframe["close"] > dataframe["close"].shift(1)).astype(int)
        dataframe["%-price_down"] = (dataframe["close"] < dataframe["close"].shift(1)).astype(int)
        
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        设置目标变量，机器学习模型将尝试预测这些目标
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]
        
        # 目标1: 预测未来N根K线的收盘价相对于当前收盘价的变化率
        dataframe["&-s_close"] = (
            dataframe["close"]
            .shift(-label_period)
            .rolling(label_period)
            .mean()
            / dataframe["close"]
            - 1
        )
        
        # 目标2: 预测未来N根K线的价格波动范围
        dataframe["&-s_range"] = (
            dataframe["high"]
            .shift(-label_period)
            .rolling(label_period)
            .max()
            -
            dataframe["low"]
            .shift(-label_period)
            .rolling(label_period)
            .min()
        ) / dataframe["close"]
        
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        使用FreqAI填充指标
        """
        # FreqAI将处理所有在feature_engineering_*函数中创建的特征
        dataframe = self.freqai.start(dataframe, metadata, self)
        
        return dataframe

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        """
        基于FreqAI预测的结果生成进场信号
        """
        # 初始化进场列
        df["enter_long"] = 0
        df["enter_short"] = 0
        df["enter_tag"] = ""
        
        # 添加一个新列来存储预测的可信度
        df["prediction_probability"] = abs(df["&-s_close"])
        
        # 多头条件
        enter_long_conditions = [
            df["do_predict"] == 1,  # FreqAI允许预测
            df["&-s_close"] > 0.01,  # 预测未来价格上涨大于1%
            df["volume"] > 0,  # 确保有交易量
            df["prediction_probability"] > 0.015  # 预测可信度足够高
        ]

        if enter_long_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_long_conditions), ["enter_long", "enter_tag"]
            ] = (1, "long_freqai_prediction")

        # 空头条件
        enter_short_conditions = [
            df["do_predict"] == 1,  # FreqAI允许预测
            df["&-s_close"] < -0.01,  # 预测未来价格下跌大于1%
            df["volume"] > 0,  # 确保有交易量
            df["prediction_probability"] > 0.015  # 预测可信度足够高
        ]

        if enter_short_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_short_conditions), ["enter_short", "enter_tag"]
            ] = (1, "short_freqai_prediction")

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        """
        基于FreqAI预测的结果生成出场信号
        """
        df["exit_long"] = 0
        df["exit_short"] = 0
        df["exit_tag"] = ""

        # 多头出场条件
        exit_long_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] < -0.005,  # 预测趋势反转
        ]

        if exit_long_conditions:
            df.loc[
                reduce(lambda x, y: x & y, exit_long_conditions), ["exit_long", "exit_tag"]
            ] = (1, "long_exit_freqai")

        # 空头出场条件
        exit_short_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] > 0.005,  # 预测趋势反转
        ]

        if exit_short_conditions:
            df.loc[
                reduce(lambda x, y: x & y, exit_short_conditions), ["exit_short", "exit_tag"]
            ] = (1, "short_exit_freqai")

        return df

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        # 进行最终的交易前风险检查
        if side == "long" and entry_tag == "long_freqai_prediction":
            # 获取模型的置信度
            df, last_updated = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            
            # 查看最后一行的预测概率
            if df.empty:
                return False
                
            last_candle = df.iloc[-1]
            prediction_probability = last_candle.get("prediction_probability", 0)
            
            # 只有当预测概率大于阈值时才进行交易
            if prediction_probability < 0.02:
                return False
        
        # 对空头进行类似的检查
        if side == "short" and entry_tag == "short_freqai_prediction":
            df, last_updated = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            
            if df.empty:
                return False
                
            last_candle = df.iloc[-1]
            prediction_probability = last_candle.get("prediction_probability", 0)
            
            if prediction_probability < 0.02:
                return False
        
        return True 